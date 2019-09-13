import functools
import pathlib
import aiohttp.web
from aiohttp_graphql import GraphQLView
import bs4
from graphene import Schema
from .schema import Query, MutationQuery


async def index(request, app_path):
    index = app_path / 'index.html'
    data = index.resolve().read_bytes()
    data = bs4.BeautifulSoup(data, 'html.parser')
    # data.find('body')['data-auth0-domain'] = 'ap-lektorium.eu.auth0.com'
    # data.find('body')['data-auth0-id'] = 'q2VZfTHwd5v6ay9PIzDXNoQH6CSI3IY0'
    return aiohttp.web.Response(
        body=str(data).encode('utf-8'),
        content_type='text/html',
    )


def create_app():
    from . import repo
    # repo = repo.GitRepo('gitlab/service')  # noqa: E800
    repo = repo.ListRepo(repo.SITES)  # noqa: E800
    return init_app(repo)


def init_app(repo):
    app = aiohttp.web.Application()
    app_path = pathlib.Path() / 'client' / 'build'

    app.router.add_static('/css', (app_path / 'css').resolve())
    app.router.add_static('/img', (app_path / 'img').resolve())
    app.router.add_static('/js', (app_path / 'js').resolve())

    index_handler = functools.partial(index, app_path=app_path)
    app.router.add_route('*', '/', index_handler)
    app.router.add_route('*', '/callback', index_handler)
    app.router.add_route('*', '/profile', index_handler)

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
