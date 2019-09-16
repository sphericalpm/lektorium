import functools
import logging
import sys
import aiohttp.web
import aiohttp_graphql
import bs4
import graphene
from . import schema
from . import install as client


async def index(request, app_path):
    index = app_path / 'index.html'
    data = index.resolve().read_bytes()
    data = bs4.BeautifulSoup(data, 'html.parser')
    auth0_options = {
        # 'data-auth0-domain': 'ap-lektorium.eu.auth0.com',
        # 'data-auth0-id': 'w1oxvMsFpZCW4G224I8JR7D2et9yqTYo',
        # 'data-auth0-api': 'Lektorium',
    }
    for k, v in auth0_options.items():
        data.find('body')[k] = v
    return aiohttp.web.Response(
        body=str(data).encode('utf-8'),
        content_type='text/html',
    )


def create_app():
    from . import repo
    from .repo.local import FakeServer  # noqa: F401
    # repo = repo.GitRepo('gitlab/service')  # noqa: E800
    # repo = repo.LocalRepo('gitlab', FakeServer())  # noqa: E800
    repo = repo.ListRepo(repo.SITES)  # noqa: E800
    return init_app(repo)


async def log_application_ready(app):
    logging.getLogger('lektorium').info('Lektorium started')


def init_logging(stream=sys.stderr, level=logging.DEBUG):
    stderr_handler = logging.StreamHandler(stream)
    stderr_handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    logging.basicConfig(
        level=level,
        handlers=[
            stderr_handler
        ],
    )


def init_app(repo):
    init_logging()

    app = aiohttp.web.Application()
    app_path = client.install()

    app.router.add_static('/css', (app_path / 'css').resolve())
    app.router.add_static('/img', (app_path / 'img').resolve())
    app.router.add_static('/js', (app_path / 'js').resolve())

    index_handler = functools.partial(index, app_path=app_path)
    app.router.add_route('*', '/', index_handler)
    app.router.add_route('*', '/callback', index_handler)
    app.router.add_route('*', '/profile', index_handler)

    aiohttp_graphql.GraphQLView.attach(
        app,
        schema=graphene.Schema(
            query=schema.Query,
            mutation=schema.MutationQuery,
        ),
        graphiql=True,
        context=dict(repo=repo),
    )

    app.on_startup.append(log_application_ready)

    return app
