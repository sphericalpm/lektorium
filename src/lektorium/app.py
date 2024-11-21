import enum
import functools
import json
import logging
import pathlib
import tempfile
from os import environ

import aiohttp.web
import aiohttp_graphql
import graphene
import pkg_resources
from graphql.error import format_error as format_graphql_error
from graphql.execution.executors.asyncio import AsyncioExecutor
from spherical.dev.log import init_logging

from . import proxy, repo, schema
from .auth0 import Auth0Client, FakeAuth0Client
from .jwt import GraphExecutionError, JWTMiddleware
from .repo.local import (
    AsyncDockerServer,
    AsyncLocalServer,
    FakeServer,
    FileStorage,
    GitlabStorage,
    GitStorage,
    LocalLektor,
)
from .utils import closer


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
    GITLAB = GitlabStorage


class ServerType(BaseEnum):
    FAKE = FakeServer
    ASYNC = AsyncLocalServer
    DOCKER = AsyncDockerServer


def create_app(repo_type=RepoType.LIST, auth='', repo_args=''):
    init_logging()
    auth0_client, auth0_options = None, None
    if auth:
        auth_attributes = ('domain', 'id', 'api', 'management-id', 'management-secret')
        auth_attributes = ('data-auth0-{}'.format(x) for x in auth_attributes)
        auth0_options = dict(zip(auth_attributes, auth.split(',')))
        if len(auth0_options) > 3:
            auth0_client = Auth0Client(auth0_options)

    if repo_type == RepoType.LIST:
        if repo_args:
            raise ValueError('LIST repo does not support arguments')
        lektorium_repo = repo.ListRepo(repo.SITES)
        if auth0_client is None:
            auth0_client = FakeAuth0Client()
    elif repo_type == RepoType.LOCAL:
        server_type, _, storage_config = repo_args.partition(',')
        storage_config, _, params = storage_config.partition(',')
        token, _, protocol = params.partition(',')
        server_type, _, options = server_type.partition(':')
        options = {k: v for k, v in (x.split('=') for x in options.split(':') if x)}
        server_type = ServerType.get(server_type or 'FAKE')
        server = server_type.value(**options)

        protocol = protocol or 'https'
        storage_config = storage_config or 'FILE'
        storage_type, _, storage_path = storage_config.partition('=')
        storage_class = StorageType.get(storage_type).value
        if not storage_path:
            storage_path = pathlib.Path(closer(tempfile.TemporaryDirectory()))
            storage_path = storage_class.init(storage_path)
        if storage_class is GitlabStorage:
            skip_aws = True if environ.get('LEKTORIUM_SKIP_AWS', '') == 'YES' else False
            storage = storage_class(storage_path, token, protocol, skip_aws)
        else:
            storage = storage_class(pathlib.Path(storage_path))

        sessions_root = None
        if server_type == ServerType.DOCKER:
            sessions_root = pathlib.Path('/sessions')
            if not sessions_root.exists():
                raise RuntimeError('/sessions not exists')

        lektorium_repo = repo.LocalRepo(
            storage,
            server,
            LocalLektor,
            sessions_root=sessions_root,
        )
    else:
        raise ValueError(f'repo_type not supported {repo_type}')

    logging.getLogger('lektorium').info(f'Start with {lektorium_repo}')
    return init_app(lektorium_repo, auth0_options, auth0_client)


async def log_application_ready(app):
    logging.getLogger('lektorium').info('Lektorium started')


def error_formatter(error):
    formatted = format_graphql_error(error)
    if hasattr(error, 'original_error'):
        if isinstance(error.original_error, GraphExecutionError):
            formatted['code'] = error.original_error.code
    return formatted


async def docker_handler(authorizer, request):
    _, permissions = await authorizer.info(request)
    if schema.ADMIN not in permissions:
        raise aiohttp.web.HTTPUnauthorized()
    await proxy.handler('/var/run/docker.sock', request)


def init_app(repo, auth0_options=None, auth0_client=None):
    app = aiohttp.web.Application(handler_args={'max_field_size': 16394})

    client_dir = pkg_resources.resource_filename(__name__, 'client')
    client_dir = pathlib.Path(client_dir).resolve()

    async def index(request):
        return aiohttp.web.FileResponse(client_dir / 'public' / 'index.html')

    async def auth0_config(request):
        options = {
            x: auth0_options.get(f'data-auth0-{x}', None)
            for x in ['domain', 'id', 'api']
        } if auth0_options else {}
        options = json.dumps(options)
        return aiohttp.web.Response(
            text=f'let lektoriumAuth0Config={options};',
            content_type='application/javascript',
        )

    app.router.add_route('*', '/', index)
    app.router.add_route('*', '/callback', index)
    app.router.add_route('*', '/logs', index)
    app.router.add_route('*', '/profile', index)
    app.router.add_route('GET', '/auth0-config', auth0_config)
    app.router.add_static('/components', client_dir / 'components')
    app.router.add_static('/images', client_dir / 'images')
    app.router.add_static('/scripts', client_dir / 'scripts')

    middleware = []
    if auth0_options is not None:
        authorizer = JWTMiddleware(auth0_options['data-auth0-domain'])
        middleware.append(authorizer)
        app.router.add_route(
            'GET',
            '/docker',
            functools.partial(docker_handler, authorizer),
        )

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
            auth0_client=auth0_client,
            **(
                {'user_permissions': ['admin']}
                if auth0_options is None else
                {}
            ),
        ),
        error_formatter=error_formatter,
    )

    app.on_startup.append(log_application_ready)

    return app


def main(repo_type='', auth=''):
    repo_type, _, repo_args = repo_type.partition(':')
    aiohttp.web.run_app(
        create_app(
            RepoType.get(repo_type),
            auth,
            repo_args,
        ),
        port=8000,
    )
