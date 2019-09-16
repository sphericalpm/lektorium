import aiohttp.web
from . import app
aiohttp.web.run_app(app.create_app(), port=8000)
