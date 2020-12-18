import collections
import copy

import graphene.test
import pytest
from graphql.execution.executors.asyncio import AsyncioExecutor

import lektorium.repo
import lektorium.schema
from lektorium.auth0 import FakeAuth0Client


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
                copy.deepcopy(lektorium.repo.SITES),
            ),
            'user_permissions': ['fake:permission'],
            'auth0_client': FakeAuth0Client(),
            'skip_permissions_check': True,
        },
        executor=AsyncioExecutor(),
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
            ],
        },
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
            ],
        },
    }


def test_session_edit_url(client):
    result = client.execute(r'''{
        sessions {
            editUrl
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'editUrl': 'https://cmsdciks.cms.acme.com'},
            ],
        },
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
            ],
        },
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
        },
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
            ],
        },
    }


def test_create_session_other_exist(client):
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
        },
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
        },
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
            ],
        },
    }


def test_park_unknown_session(client):
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
        },
    }, 'Server should fail to park unknown session'


def test_park_parked_session(client):
    client.execute(r'''mutation {
        parkSession(sessionId: "widgets-1") {
            ok
        }
    }''')
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
        },
    }, 'Server should fail to park parked session'


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
        },
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
            ],
        },
    }


def test_unpark_session_another_exist(client):
    client.execute(r'''mutation {
        unparkSession(sessionId: "pantssss") {
            ok
        }
    }''')
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
        },
    }, (
        'Server should fail to unpark session when there is an active session '
        'for same website'
    )


def test_unpark_unknown_session(client):
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
        },
    }, 'Server should fail to unpark unknown session'


def test_unpark_unkparked_session(client):
    result = client.execute(r'''mutation {
        unparkSession(sessionId: "widgets-1") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'unparkSession': {
                'ok': False,
            },
        },
    }, 'Server should fail to unpark session that was not parked'


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
        },
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
        },
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
            ],
        },
    }


def test_destroy_unknown_session(client):
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
        },
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
            'sessions': [{
                'productionUrl': 'https://bow.acme.com',
                'stagingUrl': 'https://bow-test.acme.com',
                'parked': False,
            }],
        },
    }


def test_broken_parked_resolve(client):
    result = client.execute(r'''{
        sites {
            sessions {
                parked
            }
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sites': [
                {'sessions': [{'parked': False}]},
                {'sessions': [{'parked': True}, {'parked': True}]},
                {'sessions': None},
            ],
        },
    }


def test_create_site(client):
    result = client.execute(r'''mutation {
        createSite(siteId:"test" siteName:"test") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSite': {
                'ok': True,
            },
        },
    }
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
                {'siteId': 'test'},
            ],
        },
    }


def test_parked_resolve(client):
    client.execute(r'''mutation {
        createSession(siteId: "uci") {
            ok
        }
    }''')
    result = client.execute(r'''{
        sites {
            sessions {
                parked
            }
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sites': [
                {'sessions': [{'parked': False}]},
                {'sessions': [
                    {'parked': True},
                    {'parked': True},
                    {'parked': False},
                ]},
                {'sessions': None},
            ],
        },
    }


def test_get_users(client):
    result = client.execute(r''' {
        users {
            userId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'users': [
                {'userId': 'test_id'},
            ],
        },
    }


def test_get_user_permissions(client):
    result = client.execute(r''' {
        userPermissions(userId: "test_id") {
            permissionName
        }
    }''')
    assert deorder(result) == {
        'data': {
            'userPermissions': [
                {'permissionName': 'Test Permission1'},
            ],
        },
    }


def test_get_api_permissions(client):
    result = client.execute(r''' {
        availablePermissions {
            value
        }
    }''')
    assert deorder(result) == {
        'data': {
            'availablePermissions': [
                {'value': 'admin'},
                {'value': 'user:bow'},
                {'value': 'user:uci'},
                {'value': 'user:ldi'},
            ],
        },
    }


def test_set_permissions(client):
    result = client.execute(r'''mutation {
        setUserPermissions(userId:"test_id", permissions:["Test Permission2"]) {
            ok
         }
    }''')
    assert deorder(result) == {
        'data': {
            'setUserPermissions': {
                'ok': True,
            },
        },
    }
    result = client.execute(r''' {
        userPermissions(userId: "test_id") {
            permissionName
        }
    }''')
    assert deorder(result) == {
        'data': {
            'userPermissions': [
                {'permissionName': 'Test Permission1'},
                {'permissionName': 'Test Permission2'},
            ],
        },
    }
    result = client.execute(r'''mutation {
        setUserPermissions(userId:"wrong_id", permissions:["Test Permission2"]) {
            ok
         }
    }''')
    assert deorder(result) == {
        'data': {
            'setUserPermissions': {
                'ok': False,
            },
        },
    }


def test_delete_permissions(client):
    client.execute(r'''mutation {
        setUserPermissions(userId:"test_id", permissions:["Test Permission2"]) {
            ok
         }
    }''')

    result = client.execute(r'''mutation {
        deleteUserPermissions(userId:"test_id", permissions:["Test Permission1"]) {
            ok
         }
    }''')
    assert deorder(result) == {
        'data': {
            'deleteUserPermissions': {
                'ok': True,
            },
        },
    }
    result = client.execute(r''' {
        userPermissions(userId: "test_id") {
            permissionName
        }
    }''')
    assert deorder(result) == {
        'data': {
            'userPermissions': [
                {'permissionName': 'Test Permission2'},
            ],
        },
    }

    result = client.execute(r'''mutation {
        deleteUserPermissions(userId:"wrong_id", permissions:["Test Permission1"]) {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'deleteUserPermissions': {
                'ok': False,
            },
        },
    }
