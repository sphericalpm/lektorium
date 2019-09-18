import abc
import asyncio
import functools
import logging
import random
import subprocess


class Server(metaclass=abc.ABCMeta):
    START_PORT = 5000
    END_PORT = 6000

    @classmethod
    def generate_port(cls, busy):
        port = None
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


class AsyncLocalServer(Server):
    COMMAND = 'lektor server -h 0.0.0.0 -p {port}'
    LOGGER = logging.getLogger()

    def __init__(self):
        self.serves = {}

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
                    await proc.wait()
                    raise RuntimeError('early process end')
            except Exception as exc:
                log.error('failed')
                started.set_exception(exc)
                raise
            log.info('started')
            started.set_result(port)
            try:
                async for line in proc.stdout:
                    pass
            finally:
                proc.terminate()
                await proc.wait()
        finally:
            log.info('finished')

    async def stop(self, path, finalizer=None):
        task, _ = self.serves[path]
        task.cancel()
        task.add_done_callback(lambda _: callable(finalizer) and finalizer())
        await task

    def serve_lektor(self, path):
        def resolver(started):
            if started.done():
                if started.exception() is not None:
                    try:
                        started.result()
                    except Exception:
                        self.LOGGER.exception('error')
                    return ('Failed to start',) * 2
                return (f'http://localhost:{started.result()}/',) * 2
            return (functools.partial(resolver, started), 'Starting')
        started = asyncio.Future()
        task = asyncio.ensure_future(self.start(path, started))
        self.serves[path] = [task, started]
        return functools.partial(resolver, started)

    serve_static = serve_lektor

    def stop_server(self, path, finalizer=None):
        result = asyncio.ensure_future(self.stop(path, finalizer))
        result.add_done_callback(lambda _: result.result())
