import enum
import logging
import pathlib
import sys
import tempfile


import aiohttp.web
import aiohttp_graphql
from graphql.execution.executors.asyncio import AsyncioExecutor
import bs4
import graphene

from lektorium.auth0 import Auth0Client, FakeAuth0Client
from lektorium.jwt import JWTMiddleware
from . import install as client, schema, repo
from .utils import closer
from .repo.local import (
    AsyncLocalServer,
    AsyncDockerServer,
    FakeServer,
    FileStorage,
    GitStorage,
    LocalLektor,
)


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


class BaseEnum(enum.Enum):
    @classmethod
    def get(cls, name):
        names = tuple(x.name for x in cls)
        if name not in names:
            cls_name, names = cls.__name__, ', '.join(names)
            msg = f'Wrong {cls_name} value "{name}" should be one of {names}'
            raise ValueError(msg)
        return cls[name]


class RepoType(BaseEnum):
    LIST = enum.auto()
    LOCAL = enum.auto()


class StorageType(BaseEnum):
    FILE = FileStorage
    GIT = GitStorage


class ServerType(BaseEnum):
    FAKE = FakeServer
    ASYNC = AsyncLocalServer
    DOCKER = AsyncDockerServer


def create_app(repo_type=RepoType.LIST, auth='', repo_args=''):
    init_logging()
    auth0_client = None
    auth0_options = None
    if auth:
        auth_attributes = ('domain', 'id', 'api', 'management-id', 'management-secret')
        auth_attributes = ('data-auth0-{}'.format(x) for x in auth_attributes)
        auth0_options = dict(zip(auth_attributes, auth.split(',')))

    if repo_type == RepoType.LIST:
        if repo_args:
            raise ValueError('LIST repo does not support arguments')
        lektorium_repo = repo.ListRepo(repo.SITES)
        auth0_client = FakeAuth0Client()
    elif repo_type == RepoType.LOCAL:
        server_type, _, storage_config = repo_args.partition(',')
        server_type = ServerType.get(server_type or 'FAKE')
        server = server_type.value()

        storage_config = storage_config or 'FILE'
        storage_type, _, storage_path = storage_config.partition('=')
        storage_class = StorageType.get(storage_type).value
        if not storage_path:
            storage_path = pathlib.Path(closer(tempfile.TemporaryDirectory()))
            storage_path = storage_class.init(storage_path)
        storage = storage_class(storage_path)

        sessions_root = None
        if server_type == ServerType.DOCKER:
            sessions_root = pathlib.Path('/sessions')
            if not sessions_root.exists():
                raise RuntimeError('/sessions not exists')

        lektorium_repo = repo.LocalRepo(
            storage,
            server,
            LocalLektor,
            sessions_root=sessions_root
        )
        auth0_client = Auth0Client(auth0_options)
    else:
        raise ValueError(f'repo_type not supported {repo_type}')

    logging.getLogger('lektorium').info(f'Start with {lektorium_repo}')
    return init_app(lektorium_repo, auth0_options, auth0_client)


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


def init_app(repo, auth0_options=None, auth0_client=None):
    app = aiohttp.web.Application()
    app_path = client.install()

    app.router.add_static('/css', (app_path / 'css').resolve())
    app.router.add_static('/img', (app_path / 'img').resolve())
    app.router.add_static('/js', (app_path / 'js').resolve())

    async def index_handler(*args, **kwargs):
        return await index(
            *args,
            **kwargs,
            app_path=app_path,
            auth0_options=auth0_options
        )

    app.router.add_route('*', '/', index_handler)
    app.router.add_route('*', '/callback', index_handler)
    app.router.add_route('*', '/profile', index_handler)

    middleware = []
    if auth0_options is not None:
        middleware.append(JWTMiddleware(auth0_options))

    aiohttp_graphql.GraphQLView.attach(
        app,
        schema=graphene.Schema(
            query=schema.Query,
            mutation=schema.MutationQuery,
        ),
        middleware=middleware,
        graphiql=True,
        executor=AsyncioExecutor(),
        context=dict(
            repo=repo,
            auth0_client=auth0_client
        ),
    )

    app.on_startup.append(log_application_ready)

    return app


def main(repo_type='', auth=''):
    repo_type, _, repo_args = repo_type.partition(':')
    aiohttp.web.run_app(
        create_app(
            RepoType.get(repo_type),
            auth,
            repo_args
        ),
        port=8000
    )
