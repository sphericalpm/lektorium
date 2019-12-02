import abc
import asyncio
import functools
import logging
import os
import pathlib
import random
import subprocess
import aiodocker
from more_itertools import one

from ...utils import flatten_options


class Server(metaclass=abc.ABCMeta):
    START_PORT = 5000
    END_PORT = 6000

    @classmethod
    def generate_port(cls, busy):
        port = None
        if not set(range(cls.START_PORT, cls.END_PORT + 1)).difference(busy):
            raise RuntimeError('No free ports available')
        while not port or port in busy:
            port = random.randint(cls.START_PORT, cls.END_PORT)
        return port

    @abc.abstractmethod
    def serve_lektor(self, path):
        pass

    @abc.abstractmethod
    def serve_static(self, path):
        pass

    @abc.abstractmethod
    def stop_server(self, path, finalizer=None):
        pass

    def __repr__(self):
        return f'{self.__class__.__name__}()'


class FakeServer(Server):
    def __init__(self):
        self.serves = {}

    def serve_lektor(self, path):
        if path in self.serves:
            raise RuntimeError()
        port = self.generate_port(list(self.serves.values()))
        self.serves[path] = port
        return f'http://localhost:{self.serves[path]}/'

    def stop_server(self, path, finalizer=None):
        self.serves.pop(path)
        callable(finalizer) and finalizer()

    serve_static = serve_lektor


class AsyncServer(Server):
    LOGGER = logging.getLogger()

    def __init__(self):
        self.serves = {}

    def serve_lektor(self, path):
        def resolver(started):
            if started.done():
                if started.exception() is not None:
                    try:
                        started.result()
                    except Exception:
                        self.LOGGER.exception('error')
                    return ('Failed to start',) * 2
                return (started.result(),) * 2
            return (functools.partial(resolver, started), 'Starting')
        started = asyncio.Future()
        task = asyncio.ensure_future(self.start(path, started))
        self.serves[path] = [lambda: task if task.cancel() else task, started]
        return functools.partial(resolver, started)

    serve_static = serve_lektor

    def stop_server(self, path, finalizer=None):
        result = asyncio.ensure_future(self.stop(path, finalizer))
        result.add_done_callback(lambda _: result.result())

    @abc.abstractmethod
    async def start(self, path, started):
        pass

    async def stop(self, path, finalizer=None):
        task_cancel, _ = self.serves[path]
        finalize = asyncio.gather(task_cancel(), return_exceptions=True)
        finalize.add_done_callback(
            lambda _: callable(finalizer) and finalizer()
        )
        await finalize


class AsyncLocalServer(AsyncServer):
    COMMAND = 'lektor server -h 0.0.0.0 -p {port}'

    async def start(self, path, started):
        log = logging.getLogger(f'Server({path})')
        log.info('starting')
        try:
            try:
                port = self.generate_port(())
                proc = await asyncio.create_subprocess_shell(
                    self.COMMAND.format(port=port),
                    cwd=path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                async for line in proc.stdout:
                    if line.strip().startswith(b'Finished prune'):
                        break
                else:
                    await proc.communicate()
                    raise RuntimeError('early process end')
            except Exception as exc:
                log.error('failed')
                started.set_exception(exc)
                return
            log.info('started')
            started.set_result(f'http://localhost:{port}/')
            try:
                async for line in proc.stdout:
                    pass
            finally:
                proc.terminate()
                await proc.communicate()
        finally:
            log.info('finished')


class AsyncDockerServer(AsyncServer):
    def __init__(
        self,
        *,
        auto_remove=True,
        image='lektorium-lektor',
        network=None,
    ):
        super().__init__()
        if not pathlib.Path('/var/run/docker.sock').exists():
            raise RuntimeError('/var/run/docker.sock not exists')
        self.auto_remove = auto_remove
        self.image = image
        self.network = network
        self.sessions_domain = os.environ.get('LEKTORIUM_SESSIONS_DOMAIN', None)

    @property
    async def network_mode(self):
        if self.network is None:
            docker = aiodocker.Docker()
            containers = (
                await c.show()
                for c in await docker.containers.list()
            )
            networks = [
                c['HostConfig']['NetworkMode']
                async for c in containers
                if c['Name'] == '/lektorium'
            ]
            self.network = one(networks)
        return self.network

    async def start(self, path, started):
        log = logging.getLogger(f'Server({path})')
        log.info('starting')
        container, stream = None, None
        try:
            try:
                session_id = pathlib.Path(path).name
                container_name = f'lektorium-lektor-{session_id}'
                labels = flatten_options(self.lektor_labels(session_id), "traefik")
                docker = aiodocker.Docker()
                container = await docker.containers.run(
                    name=container_name,
                    config=dict(
                        HostConfig=dict(
                            AutoRemove=self.auto_remove,
                            NetworkMode=await self.network_mode,
                            VolumesFrom=[
                                'lektorium',
                            ],
                        ),
                        Cmd=[
                            '--project', f'{path}',
                            'server',
                            '--host', '0.0.0.0',
                        ],
                        Labels=labels,
                        Image='lektorium-lektor',
                    ),
                )
                stream = container.log(stdout=True, follow=True)
                async for line in stream:
                    if line.strip().startswith('Finished prune'):
                        break
                else:
                    raise RuntimeError('early process end')
            except Exception as exc:
                log.error('failed')
                started.set_exception(exc)
                if container is not None:
                    await asyncio.gather(
                        container.kill(),
                        return_exceptions=True
                    )
            else:
                log.info('started')
                started.set_result(self.session_address(session_id, container_name))
                self.serves[path][0] = container.kill
            finally:
                if stream is not None:
                    await asyncio.gather(
                        stream.aclose(),
                        return_exceptions=True
                    )
        finally:
            log.info('start ended')

    def session_address(self, session_id, container_name):
        if self.sessions_domain is None:
            return f'http://{container_name}:5000/'
        return f'http://{session_id}.{self.sessions_domain}'

    def lektor_labels(self, session_id):
        if self.sessions_domain is None:
            return {}
        return {
            'enable': 'true',
            f'http.routers': {
                f'lektorium-lektor-{session_id}': {
                    'entrypoints': 'websecure',
                    'rule': f'Host(`{session_id}.{self.sessions_domain}`)',
                    'tls.certresolver': 'le',
                },
                f'lektorium-lektor-{session_id}-redir': {
                    'entrypoints': 'web',
                    'rule': f'Host(`{session_id}.{self.sessions_domain}`)',
                    'middlewares': 'lektorium-redir',
                },
            },
            f'http.services.lektorium-lektor-{session_id}.loadbalancer.server.port': '5000',
        }
