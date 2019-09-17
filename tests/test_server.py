import asyncio
import tempfile
import async_timeout
import pytest
from unittest.mock import MagicMock
from lektorium.repo.local import AsyncLocalServer


class AsyncTestServer(AsyncLocalServer):
    START_PORT = 5000
    END_PORT = 5000

    def __init__(self, command, ):
        super().__init__()
        self.COMMAND = command


@pytest.mark.asyncio
async def test_start_server_failed():
    result = AsyncTestServer('echo').serve_lektor('/tmp')
    while callable(result):
        await asyncio.sleep(0.1)
        result = result()[0]
    assert result == 'Failed to start'


@pytest.mark.asyncio
async def test_start_stop_server():
    with tempfile.TemporaryDirectory() as tmp:
        cmd = 'echo "Finished prune"; sleep 10'
        server = AsyncTestServer(cmd)
        result = server.serve_lektor(tmp)
        while callable(result):
            await asyncio.sleep(0.1)
            result = result()[0]
        assert result == 'http://localhost:5000/'
        finalizer = MagicMock()
        server = server.stop_server(tmp, finalizer=finalizer)
        async with async_timeout.timeout(2):
            while not finalizer.call_count:
                await asyncio.sleep(0.1)