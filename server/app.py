from flask import Flask, jsonify, render_template, abort
from flask_graphql import GraphQLView
from jinja2 import TemplateNotFound
from graphene import ObjectType, String, Schema, List, Field, Boolean, Mutation


# This is test backend for frontend prototype developing only!!!!
SITES = [{
    'site_name': 'Buy Our Widgets',
    'production_url': 'https://bow.acme.com',
    'staging_url': 'https://bow-test.acme.com',
    'custodian': 'Max Jekov',
    'custodian_email': 'mj@acme.com',
    'sessions': [{
        'session_id': 'widgets-1',
        'edit_url': 'https://cmsdciks.cms.acme.com',
        'view_url': 'https://cmsdciks.build.acme.com',
        'creation_time': '2019-07-19 10:33 UTC+1',
        'custodian': 'Max Jekov',
        'custodian_email': 'mj@acme.com',
    }],
}, {
    'site_name': 'Underpants Collectors International',
    'production_url': 'https://uci.com',
    'staging_url': 'https://uci-staging.acme.com',
    'custodian': 'Mikhail Vartanyan',
    'custodian_email': 'mv@acme.com',
    'sessions': [{
        'session_id': 'pantssss',
        'view_url': 'https://smthng.uci.com',
        'creation_time': '2019-07-18 11:33 UTC+1',
        'custodian': 'Brian',
        'custodian_email': 'brian@splitter.il',
        'parked_time': '2019-07-18 11:33 UTC+1',
    }],
}, {
    'site_name': 'Liver Donors Inc.',
    'production_url': 'https://liver.do',
    'staging_url': 'https://pancreas.acme.com',
    'custodian': 'Brian',
    'custodian_email': 'brian@splitter.il'
}]


# configuration
DEBUG = True


# instantiate the app
app = Flask(__name__, template_folder='../app/templates', static_folder='../app/static')
app.config.from_object(__name__)


class Site(ObjectType):
    site_name = String()
    custodian = String()
    custodian_email = String()
    production_url = String()
    staging_url = String()
    sessions = List(lambda: Session)


class Session(ObjectType):
    session_id = String()
    site_name = String()
    edit_url = String()
    view_url = String()
    creation_time = String()
    custodian = String()
    custodian_email = String()
    parked_time = String()
    production_url = String()
    staging_url = String()
    site = Field(Site)
    parked = Boolean()

    def resolve_production_url(parent, info):
        return parent.site.production_url

    def resolve_staging_url(parent, info):
        return parent.site.staging_url

    def resolve_site_name(parent, info):
        return parent.site.site_name

    def resolve_parked(parent, info):
        return not bool(parent.edit_url)


class DestroySession(Mutation):
    class Arguments:
        session_id = String()

    ok = Boolean()

    def mutate(root, info, session_id):
        sessions = [(s, x) for s in SITES for x in s.get('sessions', ())]
        for site, session in sessions:
            if session['session_id'] == session_id:
                site['sessions'] = [
                    x for x in site['session']
                    if x['session_id'] != session_id
                ]
            return DestroySession(ok=True)
        return DestroySession(ok=False)


class MutationQuery(ObjectType):
    destroy_session = DestroySession.Field()


class Query(ObjectType):
    sites = List(Site)
    sessions = List(Session, parked=Boolean(default_value=False))

    @staticmethod
    def sessions_list():
        for site in SITES:
            site = Site(**site)
            for session in site.sessions or ():
                yield dict(**session, site=site)

    def resolve_sites(root, info):
        return [Site(**x) for x in SITES]

    def resolve_sessions(root, info, parked):
        sessions = (Session(**x) for x in Query.sessions_list())
        return [x for x in sessions if bool(x.edit_url) != parked]


app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=Schema(
            query=Query,
            mutation=MutationQuery
        ),
        graphiql=True,
    )
)


@app.route('/')
def get_main():
    try:
        return render_template('index.html')
    except TemplateNotFound:
        abort(404)


if __name__ == '__main__':
    app.run()
