import abc
import asyncio
import functools
import logging
import os
import pathlib
import random
import subprocess
from datetime import datetime
from types import MappingProxyType

import aiodocker
from more_itertools import one
from spherical.dev.utils import flatten_options


EMPTY_DICT = MappingProxyType({})


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

    @property
    def sessions(self):
        raise RuntimeError('sessions tracking not implemented')

    @abc.abstractmethod
    def serve_lektor(self, path, session=EMPTY_DICT):
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

    def serve_lektor(self, path, session=EMPTY_DICT):
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

    def serve_lektor(self, path, session=EMPTY_DICT):
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
        task = asyncio.ensure_future(self.start(path, started, dict(session)))
        self.serves[path] = [lambda: task if task.cancel() else task, started]
        return functools.partial(resolver, started)

    serve_static = serve_lektor

    def stop_server(self, path, finalizer=None):
        result = asyncio.ensure_future(self.stop(path, finalizer))
        result.add_done_callback(lambda _: result.result())

    @abc.abstractmethod
    async def start(self, path, started, session):
        pass

    async def stop(self, path, finalizer=None):
        task_cancel, _ = self.serves[path]
        finalize = asyncio.gather(task_cancel(), return_exceptions=True)
        finalize.add_done_callback(
            lambda _: callable(finalizer) and finalizer(),
        )
        await finalize


class AsyncLocalServer(AsyncServer):
    COMMAND = 'lektor server -h 0.0.0.0 -p {port}'

    async def start(self, path, started, session):
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
    LEKTOR_PORT = 5000
    LABEL_PREFIX = 'lektorium'

    def __init__(
        self,
        *,
        auto_remove=True,
        lektor_image='lektorium-lektor',
        network=None,
        server_container='lektorium',
    ):
        super().__init__()
        if not pathlib.Path('/var/run/docker.sock').exists():
            raise RuntimeError('/var/run/docker.sock not exists')
        self.auto_remove = auto_remove
        self.lektor_image = lektor_image
        self.network = network
        self.sessions_domain = os.environ.get('LEKTORIUM_SESSIONS_DOMAIN', None)
        self.server_container = server_container

    @property
    async def sessions(self):
        def parse(containers):
            for x in containers:
                if f'{self.LABEL_PREFIX}.edit_url' not in x['Config']['Labels']:
                    continue
                session = {
                    k[len(self.LABEL_PREFIX) + 1 :]: v
                    for k, v in x['Config']['Labels'].items()
                    if k.startswith(self.LABEL_PREFIX)
                }
                if 'creation_time' in session:
                    creation_time = float(session['creation_time'])
                    creation_time = datetime.fromtimestamp(creation_time)
                    session['creation_time'] = creation_time
                yield session

        docker = aiodocker.Docker()
        containers = (await c.show() for c in await docker.containers.list())
        return list(parse([x async for x in containers]))

    @property
    async def network_mode(self):
        if self.network is None:
            docker = aiodocker.Docker()
            containers = (await c.show() for c in await docker.containers.list())
            networks = [
                c['HostConfig']['NetworkMode'] async for c in containers if c['Name'] == f'/{self.server_container}'
            ]
            self.network = one(networks)
        return self.network

    def env_vars(self, session):
        return []

    async def start(self, path, started, session):
        log = logging.getLogger(f'Server({path})')
        log.info('starting')
        container, stream = None, None
        try:
            try:
                session_id = pathlib.Path(path).name
                container_name = f'{self.lektor_image}-{session_id}'
                labels = flatten_options(self.lektor_labels(session_id), 'traefik')
                session = self.update_session_params(session_id, container_name, session)
                labels.update(flatten_options(session, self.LABEL_PREFIX))
                docker = aiodocker.Docker()
                container = await docker.containers.run(
                    name=container_name,
                    config=dict(
                        HostConfig=dict(
                            AutoRemove=self.auto_remove,
                            NetworkMode=await self.network_mode,
                            VolumesFrom=[
                                self.server_container,
                            ],
                        ),
                        Cmd=['--project', f'{path}', 'server', '--host', '0.0.0.0'],
                        Env=self.env_vars(session),
                        Labels=labels,
                        Image=self.lektor_image,
                    ),
                )
                stream = container.log(stdout=True, stderr=True, follow=True)
                async for line in stream:
                    logging.debug(line.strip())
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
                        return_exceptions=True,
                    )
            else:
                log.info('started')
                started.set_result((session['edit_url'], session['preview_url'], session['legacy_admin_url']))
                self.serves[path][0] = container.kill
            finally:
                if stream is not None:
                    await asyncio.gather(
                        stream.aclose(),
                        return_exceptions=True,
                    )
        finally:
            log.info('start ended')

    async def stop(self, path, finalizer=None):
        if path in self.serves:
            return await super().stop(path, finalizer)
        session_id = path.name
        container_name = f'{self.lektor_image}-{session_id}'
        for container in await aiodocker.Docker().containers.list():
            info = await container.show()
            if info['Name'] == f'/{container_name}':
                await container.kill()
        callable(finalizer) and finalizer()

    def update_session_params(self, session_id, container_name, session):
        session = {
            **session,
            'edit_url': self.session_address(session_id, container_name),
            'preview_url': '',
            'legacy_admin_url': '',
        }
        if 'creation_time' in session:
            session['creation_time'] = str(session['creation_time'].timestamp())
        session.pop('parked_time', None)
        return session

    def session_address(self, session_id, container_name):
        if self.sessions_domain is None:
            return f'https://{container_name}:{self.LEKTOR_PORT}/'
        return f'http://{session_id}.{self.sessions_domain}'

    def lektor_labels(self, session_id):
        if self.sessions_domain is None:
            return {}
        route_name = f'{self.lektor_image}-{session_id}'
        skip_resolver = os.environ.get('LEKTORIUM_SKIP_RESOLVER', False)
        return {
            'enable': 'true',
            'http.routers': {
                route_name: {
                    'entrypoints': 'websecure',
                    'rule': f'Host(`{session_id}.{self.sessions_domain}`)',
                    'tls': {},
                    'tls.domains[0].main': f'*.{self.sessions_domain}',
                    **({} if skip_resolver else {'tls.certresolver': 'le'}),
                },
            },
            'http.middlewares.no-cache-headers.headers.customresponseheaders': {
                'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            },
            'http.middlewares.retry-app.retry': {
                'attempts': '5',
                'initialinterval': '200ms',
            },
            f'http.services.{route_name}.loadbalancer.server.port': f'{self.LEKTOR_PORT}',
        }


class AsyncDockerServerLectern(AsyncDockerServer):
    def __init__(self, *, lektor_image='lektorium-lectern', **kwargs):
        super().__init__(lektor_image=lektor_image, **kwargs)

    def env_vars(self, session):
        return [
            f'LECTERN_TINYMCE_KEY={os.environ.get("TINYMCE_KEY", "")}',
            f'LECTERN_REDIRECT_URL={session["preview_url"]}',
        ]

    def update_session_params(self, session_id, container_name, session):
        session = super().update_session_params(session_id, container_name, session)
        session['preview_url'] = self.preview_session_address(session_id, container_name)
        session['legacy_admin_url'] = self.legacy_admin_session_address(session_id, container_name)
        return session

    def session_address(self, session_id, container_name):
        if self.sessions_domain is None:
            return f'https://{container_name}:{self.LEKTOR_PORT}/lectern-admin/ui/'
        return f'http://{session_id}.{self.sessions_domain}/lectern-admin/ui/'

    def preview_session_address(self, session_id, container_name):
        if self.sessions_domain is None:
            return f'https://{container_name}:{self.LEKTOR_PORT}/'
        return f'http://{session_id}-preview.{self.sessions_domain}'

    def legacy_admin_session_address(self, session_id, container_name):
        if self.sessions_domain is None:
            return f'https://{container_name}:{self.LEKTOR_PORT}/admin/'
        return f'http://{session_id}-legacy-admin.{self.sessions_domain}/admin/'

    def lektor_labels(self, session_id):
        if self.sessions_domain is None:
            return {}
        labels = super().lektor_labels(session_id)
        route_name = one(labels['http.routers'].keys())
        labels[f'http.services.{route_name}.loadbalancer.server.port'] = f'{self.LEKTOR_PORT}'
        labels['http.routers'][f'{route_name}']['service'] = f'{route_name}'
        labels['http.routers'][f'{route_name}']['middlewares'] = 'retry-app'

        labels[f'http.services.{route_name}-preview.loadbalancer.server.port'] = f'{self.LEKTOR_PORT}'
        labels['http.routers'][f'{route_name}-preview'] = {**labels['http.routers'][route_name]}
        labels['http.routers'][f'{route_name}-preview']['rule'] = f'Host(`{session_id}-preview.{self.sessions_domain}`)'
        labels['http.routers'][f'{route_name}-preview']['service'] = f'{route_name}-preview'
        labels['http.routers'][f'{route_name}-preview']['middlewares'] = 'retry-app'

        labels[f'http.services.{route_name}-legacy-admin.loadbalancer.server.port'] = f'{self.LEKTOR_PORT}'
        labels['http.routers'][f'{route_name}-legacy-admin'] = {**labels['http.routers'][route_name]}
        labels['http.routers'][f'{route_name}-legacy-admin']['rule'] = (
            f'Host(`{session_id}-legacy-admin.{self.sessions_domain}`)'
        )
        labels['http.routers'][f'{route_name}-legacy-admin']['service'] = f'{route_name}-legacy-admin'
        labels['http.routers'][f'{route_name}-legacy-admin']['middlewares'] = 'retry-app'
        return labels
