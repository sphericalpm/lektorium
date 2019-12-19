import copy
import pytest
import collections
from os import environ

import graphene.test
from graphql.execution.executors.asyncio import AsyncioExecutor
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
def client_with_permissions():
    environ.pop('CHECKPERMISSIONS', '')
    return graphene.test.Client(
        graphene.Schema(
            query=lektorium.schema.Query,
            mutation=lektorium.schema.MutationQuery,
        ),
        context={
            'repo': lektorium.repo.ListRepo(
                copy.deepcopy(lektorium.repo.SITES)
            ),
            'user_permissions': [
                'read:sites',
                'read:sessions',
                'read:users',
                'read:user-permissions',
                'read:all-permissions',
                'read:releases',

                'add:permission',
                'add:release',
                'add:session',
                'add:site',
                'delete:permission',
                'delete:session',
                'edit:session',
            ]
        },
        executor=AsyncioExecutor(),
    )


@pytest.fixture
def client_without_permissions():
    environ.pop('CHECKPERMISSIONS', '')
    return graphene.test.Client(
        graphene.Schema(
            query=lektorium.schema.Query,
            mutation=lektorium.schema.MutationQuery,
        ),
        context={
            'repo': lektorium.repo.ListRepo(
                copy.deepcopy(lektorium.repo.SITES)
            ),
            'user_permissions': ['fake:permission'],
        },
        executor=AsyncioExecutor(),
    )


def test_query_with_permissions(client_with_permissions):
    result = client_with_permissions.execute(r'''{
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


def test_query_without_permissions(client_without_permissions):
    result = client_without_permissions.execute(r'''{
        sites {
            siteId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sites': [

            ]
        }
    }


def test_mutation_with_permissions(client_with_permissions):
    result = client_with_permissions.execute(r'''mutation {
        createSite(siteId:"test" siteName:"test") {
            ok,
            nopermission,
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSite': {
                'ok': True,
                'nopermission': False,
            },
        }
    }


def test_mutation_without_permissions(client_without_permissions):
    result = client_without_permissions.execute(r'''mutation {
        createSite(siteId:"test" siteName:"test") {
            ok,
            nopermission,
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSite': {
                'ok': False,
                'nopermission': True,
            },
        }
    }
