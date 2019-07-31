#! /usr/bin/env python3.7
from aiohttp import web

from routes import routes
from settings import *


app = web.Application()

for route in routes:
    app.router.add_route(route[0], route[1], route[2], name=route[3])

web.run_app(app)
