import copy
import pytest
import collections
import graphene.test
import lektorium.schema
import lektorium.repo


def deorder(obj):
    '''Removes OrderedDict's in object tree'''
    if isinstance(obj, (collections.OrderedDict, dict)):
        return {k: deorder(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deorder(k) for k in obj]
    return obj


@pytest.fixture
def client():
    return graphene.test.Client(
        graphene.Schema(
            query=lektorium.schema.Query,
            mutation=lektorium.schema.MutationQuery,
        ),
        context={
            'repo': lektorium.repo.ListRepo(
                copy.deepcopy(lektorium.repo.SITES)
            )
        }
    )


def test_query_sites(client):
    result = client.execute(r'''{
        sites {
            siteId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sites': [
                {'siteId': 'bow'},
                {'siteId': 'uci'},
                {'siteId': 'ldi'},
            ]
        }
    }


def test_query_edit_session(client):
    result = client.execute(r'''{
        sessions {
            sessionId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'sessionId': 'widgets-1'},
            ]
        }
    }


def test_query_parked_session(client):
    result = client.execute(r'''{
        sessions(parked: true) {
            sessionId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'sessionId': 'pantssss'},
                {'sessionId': 'pantss1'},
            ]
        }
    }


def test_create_session(client):
    result = client.execute(r'''mutation {
        createSession(siteId: "uci") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSession': {
                'ok': True,
            },
        }
    }
    result = client.execute(r'''{
        sessions {
            siteName
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'siteName': 'Buy Our Widgets'},
                {'siteName': 'Underpants Collectors International'},
            ]
        }
    }
    result = client.execute(r'''mutation {
        createSession(siteId: "bow") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSession': {
                'ok': False,
            },
        }
    }, 'Server should fail to create session if another already exists'


def test_park_session(client):
    result = client.execute(r'''mutation {
        parkSession(sessionId: "widgets-1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'parkSession': {
                'ok': True,
            },
        }
    }
    result = client.execute(r'''{
        sessions(parked: true) {
            sessionId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'sessionId': 'widgets-1'},
                {'sessionId': 'pantssss'},
                {'sessionId': 'pantss1'},
            ]
        }
    }
    result = client.execute(r'''mutation {
        parkSession(sessionId: "test12345") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'parkSession': {
                'ok': False,
            },
        }
    }, 'Server should fail to park unknown session'
    result = client.execute(r'''mutation {
        parkSession(sessionId: "widgets-1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'parkSession': {
                'ok': False,
            },
        }
    }


def test_unpark_session(client):
    result = client.execute(r'''mutation {
        unparkSession(sessionId: "pantssss") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'unparkSession': {
                'ok': True,
            },
        }
    }
    result = client.execute(r'''{
        editSessions: sessions(parked: false) {
            sessionId
        }
        parkedSessions: sessions(parked: true) {
            sessionId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'editSessions': [
                {'sessionId': 'widgets-1'},
                {'sessionId': 'pantssss'},
            ],
            'parkedSessions': [
                {'sessionId': 'pantss1'},
            ]
        }
    }
    result = client.execute(r'''mutation {
        unparkSession(sessionId: "pantss1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'unparkSession': {
                'ok': False,
            },
        }
    }, 'Server should fail to unpark session when there is an active session for same website'
    result = client.execute(r'''mutation {
        unparkSession(sessionId: "test12345") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'unparkSession': {
                'ok': False,
            },
        }
    }, 'Server should fail to unpark unknown session'


def test_stage(client):
    result = client.execute(r'''mutation {
        stage(sessionId: "widgets-1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'stage': {
                'ok': True,
            },
        }
    }


def test_request_release(client):
    result = client.execute(r'''mutation {
        requestRelease(sessionId: "widgets-1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'requestRelease': {
                'ok': True,
            },
        }
    }


def test_destroy_session(client):
    result = client.execute(r'''mutation {
        destroySession(sessionId: "pantss1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'destroySession': {
                'ok': True,
            },
        }
    }
    result = client.execute(r'''{
        sessions(parked: true) {
            sessionId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'sessionId': 'pantssss'},
            ]
        }
    }
    result = client.execute(r'''mutation {
        destroySession(sessionId: "test12345") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'destroySession': {
                'ok': False,
            },
        }
    }, 'Server should fail to destroy unknown session'


def test_resolve_funcs(client):
    result = client.execute(r'''{
        sessions {
            productionUrl
            stagingUrl
            parked
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'productionUrl': 'https://bow.acme.com'},
                {'stagingUrl': 'https://bow-test.acme.com'},
                {'parked': False},
            ]
        }
    }
