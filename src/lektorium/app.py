import enum
import functools
import logging
import sys


import aiohttp.web
import aiohttp_graphql
from graphql.execution.executors.asyncio import AsyncioExecutor
import bs4
import graphene

from . import install as client
from . import schema


async def index(request, app_path, auth0_options=None):
    index = app_path / 'index.html'
    data = index.resolve().read_bytes()
    data = bs4.BeautifulSoup(data, 'html.parser')
    if auth0_options is not None:
        for k, v in auth0_options.items():
            data.find('body')[k] = v
    return aiohttp.web.Response(
        body=str(data).encode('utf-8'),
        content_type='text/html',
    )


class RepoType(enum.Enum):
    LIST = enum.auto()
    LOCAL_FAKE = enum.auto()
    LOCAL_ASYNC = enum.auto()
    GIT = enum.auto()


def create_app(repo_type=RepoType.LIST, auth=''):
    from . import repo
    if repo_type == RepoType.LIST:
        repo = repo.ListRepo(repo.SITES)
    elif repo_type in (RepoType.LOCAL_FAKE, RepoType.LOCAL_ASYNC):
        from .repo.local import LocalLektor
        if repo_type == RepoType.LOCAL_FAKE:
            from .repo.local import FakeServer
            server = FakeServer
        else:
            from .repo.local import AsyncLocalServer
            server = AsyncLocalServer()
        repo = repo.LocalRepo('gitlab', server, LocalLektor)
    else:
        repo = repo.GitRepo('gitlab/service')
    auth_attributes = ('domain', 'id', 'api')
    auth_attributes = ('data-auth0-{}'.format(x) for x in auth_attributes)
    auth0_options = dict(zip(auth_attributes, auth.split(',')))
    return init_app(repo, auth0_options)


async def log_application_ready(app):
    logging.getLogger('lektorium').info('Lektorium started')


def init_logging(stream=sys.stderr, level=logging.DEBUG):
    stderr_handler = logging.StreamHandler(stream)
    stderr_handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    logging.basicConfig(
        level=level,
        handlers=[
            stderr_handler
        ],
    )


def init_app(repo, auth0_options=None):
    init_logging()

    app = aiohttp.web.Application()
    app_path = client.install()

    app.router.add_static('/css', (app_path / 'css').resolve())
    app.router.add_static('/img', (app_path / 'img').resolve())
    app.router.add_static('/js', (app_path / 'js').resolve())

    index_handler = functools.partial(
        index, app_path=app_path,
        auth0_options=auth0_options,
    )
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
        executor=AsyncioExecutor(),
        context=dict(repo=repo),
    )

    app.on_startup.append(log_application_ready)

    return app


def main(repo_type='', auth=''):
    repo_type_names = [x.name for x in RepoType]
    if repo_type not in repo_type_names:
        message = 'Please provide repo type as argument. Use one of: {}'
        print(message.format(', '.join(repo_type_names)), file=sys.stderr)
        sys.exit(1)
    repo_type = RepoType[repo_type]
    aiohttp.web.run_app(create_app(repo_type, auth), port=8000)
