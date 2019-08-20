from aiohttp import web
from routes import routes


app = web.Application()

for route in routes:
    app.router.add_route(route[0], route[1], route[2], name=route[3])

web.run_app(app)

