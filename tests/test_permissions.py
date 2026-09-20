import collections
import copy

import graphene.test
import pytest
from graphql.execution.executors.asyncio import AsyncioExecutor

import lektorium.repo
import lektorium.schema
from lektorium.app import error_formatter

permission_query_todo = pytest.mark.xfail(
    reason='TODO in schema.py: permission decorator treats GraphQL root as info',
    strict=True,
)


def deorder(obj):
    '''Removes OrderedDict's in object tree'''
    if isinstance(obj, (collections.OrderedDict, dict)):
        return {k: deorder(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deorder(k) for k in obj]
    return obj


@pytest.fixture
def client_with_permissions():
    return graphene.test.Client(
        graphene.Schema(
            query=lektorium.schema.Query,
            mutation=lektorium.schema.MutationQuery,
        ),
        context={
            'repo': lektorium.repo.ListRepo(
                copy.deepcopy(lektorium.repo.SITES),
            ),
            'user_permissions': [
                'user:ldi',
            ],
        },
        executor=AsyncioExecutor(),
    )


@pytest.fixture
def client_without_permissions():
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
        },
        executor=AsyncioExecutor(),
        format_error=error_formatter,
    )


@pytest.fixture
def client_admin():
    return graphene.test.Client(
        graphene.Schema(
            query=lektorium.schema.Query,
            mutation=lektorium.schema.MutationQuery,
        ),
        context={
            'repo': lektorium.repo.ListRepo(
                copy.deepcopy(lektorium.repo.SITES),
            ),
            'user_permissions': [lektorium.schema.ADMIN],
        },
        executor=AsyncioExecutor(),
    )


@permission_query_todo
def test_admin_query(client_admin):
    result = client_admin.execute(r'''{
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


def test_admin_mutation(client_admin):
    result = client_admin.execute(r'''mutation {
        createSite(siteId:"test" siteName:"test") {
            ok,
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSite': {
                'ok': True,
            },
        },
    }


def test_delete_site_requires_admin(client_with_permissions):
    result = client_with_permissions.execute(r'''mutation {
        deleteSite(siteId:"ldi") {
            ok
        }
    }''')
    assert result['errors']
    assert not result['data']['deleteSite']


def test_admin_can_delete_site(client_admin):
    result = client_admin.execute(r'''mutation {
        deleteSite(siteId:"ldi") {
            ok
        }
    }''')
    assert deorder(result) == {
        'data': {
            'deleteSite': {
                'ok': True,
            },
        },
    }


@pytest.fixture
def anonymous_client():
    return graphene.test.Client(
        graphene.Schema(
            query=lektorium.schema.Query,
            mutation=lektorium.schema.MutationQuery,
        ),
        context={
            'repo': lektorium.repo.ListRepo(
                copy.deepcopy(lektorium.repo.SITES),
            ),
            'user_permissions': [],
        },
        executor=AsyncioExecutor(),
        format_error=error_formatter,
    )


@permission_query_todo
def test_query_no_permissions(anonymous_client):
    result = anonymous_client.execute(r'''{
        sites {
            siteId
        }
    }''')
    assert result['errors'][0]['code'] == 403
    assert not result['data']['sites']


def test_mutation_no_permissions(anonymous_client):
    result = anonymous_client.execute(r'''mutation {
        createSite(siteId:"test" siteName:"test") {
            ok,
        }
    }''')
    assert result['errors'][0]['code'] == 403
    assert not result['data']['createSite']


@permission_query_todo
def test_query_with_permissions(client_with_permissions):
    result = client_with_permissions.execute(r'''{
        sites {
            siteId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sites': [
                {'siteId': 'ldi'},
            ],
        },
    }


@permission_query_todo
def test_query_without_permissions(client_without_permissions):
    result = client_without_permissions.execute(r'''{
        sites {
            siteId
        }
    }''')
    assert deorder(result) == {
        'data': {
            'sites': [],
        },
    }


def test_mutation_with_permissions(client_with_permissions):
    result = client_with_permissions.execute(r'''mutation {
        createSession(siteId: "ldi") {
            ok,
        }
    }''')
    assert deorder(result) == {
        'data': {
            'createSession': {
                'ok': True,
            },
        },
    }


def test_mutation_without_permissions(client_without_permissions):
    result = client_without_permissions.execute(r'''mutation {
        createSite(siteId:"test" siteName:"test") {
            ok,
        }
    }''')
    assert result['errors'][0]['code'] == 403
    assert not result['data']['createSite']
