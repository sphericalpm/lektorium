import asyncio
import logging

import aiohttp.web


async def handler(path, request):
    logging.debug('New connection received')
    try:
        ws = aiohttp.web.WebSocketResponse()
        reader, writer = await asyncio.open_unix_connection(path)
        await ws.prepare(request)
        await streamer(ws, reader, writer)
        return ws
    finally:
        logging.debug('Connection closed')


async def streamer(
    ws,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
):
    create_task = asyncio.get_event_loop().create_task
    other = create_task(tcp2ws(ws, reader))

    def ws_close(*args, **kwargs):
        create_task(ws.close())
    other.add_done_callback(ws_close)

    try:
        await ws2tcp(ws, writer)
    finally:
        other.cancel()
        await other


async def ws2tcp(
    ws,
    writer: asyncio.StreamWriter,
):
    try:
        async for data in ws:
            if data.type == aiohttp.WSMsgType.BINARY:
                writer.write(data.data)
            else:
                raise RuntimeError(f'{data.type} not supported')
    finally:
        await writer.drain()
        writer.close()
        await writer.wait_closed()


async def tcp2ws(
    ws,
    reader: asyncio.StreamReader,
):
    while True:
        data = await reader.read(1024)
        if not data:
            break
        await ws.send_bytes(data)
