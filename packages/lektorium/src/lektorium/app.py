import pathlib
from flask import Flask, render_template, abort
from flask_graphql import GraphQLView
from jinja2 import TemplateNotFound
from .schema import Schema, Query, MutationQuery


# configuration
DEBUG = True


# instantiate the app
app_path = pathlib.Path() / 'app'
app = Flask(
    __name__,
    template_folder=(app_path / 'templates').resolve(),
    static_folder=(app_path / 'static').resolve(),
)
app.config.from_object(__name__)


repo = None
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=Schema(
            query=Query,
            mutation=MutationQuery
        ),
        graphiql=True,
        get_context=lambda: dict(repo=repo),
    ),
)


@app.route('/')
def get_main():
    return render_template('index.html')
