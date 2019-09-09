from flask import Flask, jsonify, render_template, abort
from flask_graphql import GraphQLView
from jinja2 import TemplateNotFound
from graphene import ObjectType, String, Schema, List, Field, Boolean


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
        schema=Schema(query=Query),
        graphiql=True,
    )
)


@app.route('/')
def get_main():
    try:
        return render_template('index.html')
    except TemplateNotFound:
        abort(404)

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@app.route('/edits', methods=['GET'])
def get_edit_sessions():
    sessions = []
    for site in SITES:
        for site_session in site.get('sessions', ()):
            if not site_session.get('edit_url'):
                continue
            site_session = dict(site_session)
            site_session['admin_url'] = site_session.pop('edit_url', None)
            site_session['build_url'] = site_session.pop('view_url', None)
            site_session['production_url'] = site['production_url']
            site_session['staging_url'] = site['staging_url']
            sessions.append(site_session)
    return jsonify(sessions)


@app.route('/parked', methods=['GET'])
def get_parked_session():
    sessions = []
    for site in SITES:
        for site_session in site.get('sessions', ()):
            if site_session.get('parked_time'):
                continue
            site_session = dict(
                session_id=site_session['session_id'],
                site_name=site['site_name'],
                creation_time=site_session['creation_time'],
            )
            sessions.append(site_session)
    return jsonify(sessions)


if __name__ == '__main__':
    app.run()
