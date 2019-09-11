from collections import OrderedDict
from graphene import Schema
from graphene.test import Client
from lektorium.schema import Query, MutationQuery
from lektorium.repo import ListRepo, SITES


def deorder(obj):
    '''Removes OrderedDict's in object tree'''
    if isinstance(obj, (OrderedDict, dict)):
        return {k: deorder(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deorder(k) for k in obj]
    return obj


def test_query_sites():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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


def test_query_edit_session():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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


def test_query_parked_session():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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


def test_create_session():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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
    }


def test_park_session():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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
    }


def test_unpark_session():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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
        sessions {
            sessionId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sessions': [
                {'sessionId': 'widgets-1'},
                {'sessionId': 'pantssss'},
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
    }


def test_stage():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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


def test_request_release():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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


def test_destroy_session():
    client = Client(Schema(
        query=Query,
        mutation=MutationQuery,
    ), context={'repo': ListRepo(SITES)})
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
    }
