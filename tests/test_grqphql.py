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


def test_destroy_session():
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
