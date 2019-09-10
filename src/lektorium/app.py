import functools
import pathlib
import aiohttp.web
from aiohttp_graphql import GraphQLView
from .schema import Schema, Query, MutationQuery


async def index(request, app_path):
    index = app_path / 'templates' / 'index.html'
    return aiohttp.web.FileResponse(index.resolve())


def create_app():
    from .repo import ListRepo, GitRepo, SITES
    # repo = GitRepo('gitlab/service')
    repo = ListRepo(SITES)
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
