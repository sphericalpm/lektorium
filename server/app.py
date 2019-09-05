from flask import Flask, jsonify
from flask_cors import CORS

# This is test backend for frontend prototype developing only!!!!
AVAILABLE_SITES = [
    {
        "site_name": "Buy Our Widgets",
        "production_url": "https://bow.acme.com",
        "staging_url": "https://bow-test.acme.com",
        "custodian": "Max Jekov", "custodian_email": "mj@acme.com"
    },
    {
        "site_name": "Underpants Collectors International",
        "production_url": "https://uci.com",
        "staging_url": "https://uci-staging.acme.com",
        "custodian": "Mikhail Vartanyan",
        "custodian_email": "mv@acme.com"
    },
    {
        "site_name": "Liver Donors Inc.",
        "production_url": "https://liver.do",
        "staging_url": "https://pancreas.acme.com",
        "custodian": "Brian",
        "custodian_email": "brian@splitter.il"
    },
]

EDIT_SESSIONS = [
    {
        "session_id": "widgets-1",
        "admin_url": "https://cmsdciks.cms.acme.com",
        "build_url": "https://cmsdciks.build.acme.com",
        "site_name": "Buy Our Widgets",
        "creation_time": "2019-07-19 10:33 UTC+1",
        "custodian": "Max Jekov",
        "custodian_email": "mj@acme.com",
        "production_url": "https://bow.acme.com",
        "staging_url": "https://bow-test.acme.com",
    },
]

PARKED_SESSION = [
    {
        "session_id": "widgets-1",
        "site_name": "Buy Our Widgets",
        "creation_time": "2019-07-19 10:33 UTC+1"
    },
    {
        "session_id": "pantssss",
        "site_name": "Underpants Collectors International",
        "creation_time": "2019-07-18 11:33 UTC+1"
    },
]

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app)


# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@app.route('/sites', methods=['GET'])
def get_sites():
    return jsonify(AVAILABLE_SITES)


@app.route('/edits', methods=['GET'])
def get_edit_sessions():
    return jsonify(EDIT_SESSIONS)


@app.route('/parked', methods=['GET'])
def get_parked_session():
    return jsonify(PARKED_SESSION)


if __name__ == '__main__':
    app.run()
