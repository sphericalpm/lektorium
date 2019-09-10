import functools
import pathlib
import aiohttp.web
from aiohttp_graphql import GraphQLView
from graphene import Schema
from .schema import Query, MutationQuery


async def index(request, app_path):
    index = app_path / 'templates' / 'index.html'
    return aiohttp.web.FileResponse(index.resolve())


def create_app():
    from . import repo
    # repo = repo.GitRepo('gitlab/service')  # noqa: E800
    repo = repo.ListRepo(repo.SITES)  # noqa: E800
    return init_app(repo)


def init_app(repo):
    app = aiohttp.web.Application()
    app_path = pathlib.Path() / 'app'
    app.router.add_static('/static', (app_path / 'static').resolve())
    app.router.add_route('*', '/', functools.partial(index, app_path=app_path))
    GraphQLView.attach(
        app,
        schema=Schema(
            query=Query,
            mutation=MutationQuery,
        ),
        graphiql=True,
        context=dict(repo=repo),
    )
    return app
