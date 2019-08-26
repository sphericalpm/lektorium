import aiohttp_cors
from aiohttp import web
from routes import routes


app = web.Application()

for route in routes:
    app.router.add_route(route[0], route[1], route[2], name=route[3])

# import asyncio
# @asyncio.coroutine
# def handler(request):
#     return web.Response(
#         text="Hello!",
#         headers={
#             "X-Custom-Server-Header": "Custom data",
#         })
#
# app = web.Application()
#
# cors = aiohttp_cors.setup(app, defaults={
#         "*": aiohttp_cors.ResourceOptions(
#                 allow_credentials=True,
#                 expose_headers="*",
#                 allow_headers="*",
#             )
#     })
#
# resource = cors.add(app.router.add_resource("/hello"))
# cors.add(resource.add_route("GET", handler))
# cors.add(resource.add_route("PUT", handler))
# cors.add(resource.add_route("POST", handler))
# cors.add(resource.add_route("DELETE", handler))



web.run_app(app)
