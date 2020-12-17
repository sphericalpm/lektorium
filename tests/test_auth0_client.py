import functools

import pytest
from aioresponses import aioresponses

from lektorium.auth0 import Auth0Client, Auth0Error, FakeAuth0Client


TEST_TOKEN = {'access_token': 'test_token'}
TEST_AUTH_DATA = {
    'data-auth0-domain': 'testdomain',
    'data-auth0-api': 'testapi',
    'data-auth0-management-id': 'testid',
    'data-auth0-management-secret': 'testsecret',
}


@pytest.fixture
def auth0_client():
    test_auth_data = {
        'data-auth0-domain': 'testdomain',
        'data-auth0-api': 'testapi',
        'data-auth0-management-id': 'testid',
        'data-auth0-management-secret': 'testsecret',
    }
    return Auth0Client(test_auth_data)


@pytest.fixture
def fake_auth0_client():
    return FakeAuth0Client()


@pytest.mark.asyncio
async def test_fake_auth_token(fake_auth0_client):
    token = await fake_auth0_client.auth_token
    assert token == 'test_token'


@pytest.mark.asyncio
async def test_fake_get_user_permissions(fake_auth0_client):
    with pytest.raises(Auth0Error):
        await fake_auth0_client.get_user_permissions('wrong_id')


@pytest.fixture
def mocked(auth0_client):
    with aioresponses() as mocked:
        mocked.post(auth0_client.token_url, status=200, payload=TEST_TOKEN)
        yield mocked


@pytest.mark.asyncio
async def test_auth_token(auth0_client, mocked):
    assert (await auth0_client.auth_token) == 'test_token'
    mocked.post(auth0_client.token_url, status=404)
    auth0_client.token_time = 0
    requests = list(mocked.requests.values())
    assert len(requests) == 1
    assert len(requests[0]) == 1
    request = requests[0][0]
    assert request.kwargs['json']['audience'] == f'{auth0_client.audience}/'
    with pytest.raises(Auth0Error):
        await auth0_client.auth_token


@pytest.mark.asyncio
async def test_get_users(auth0_client, mocked):
    url = f'{auth0_client.audience}/users?fields=name,nickname,email,user_id&per_page=100'
    users_response = [{
        'username': 'mjekov',
    }]
    mocked.get(url, status=200, payload=users_response)
    assert (await auth0_client.get_users()) == users_response
    mocked.get(url, status=400)
    auth0_client._cache.pop(('users',), None)
    with pytest.raises(Auth0Error):
        await auth0_client.get_users()


@pytest.mark.asyncio
async def test_get_user_permissions(auth0_client, mocked):
    url = f'{auth0_client.audience}/users/user_id/permissions?per_page=100'
    permissions_response = [{
        'permission_name': 'read:projects',
    }]
    mocked.get(url, status=200, payload=permissions_response)
    response = await auth0_client.get_user_permissions('user_id')
    assert response == permissions_response
    auth0_client._cache.pop(('user_permissions', 'user_id'), None)
    mocked.get(url, status=400)
    with pytest.raises(Auth0Error):
        await auth0_client.get_user_permissions('user_id')


@pytest.mark.asyncio
async def test_set_user_permissions(auth0_client, mocked):
    api_permissions_url = f'{auth0_client.audience}/resource-servers?per_page=100'
    mocked.get(
        api_permissions_url,
        status=200,
        payload=[{
            'identifier': auth0_client.api_id,
            'scopes': [{
                'value': 'perm-id',
                'description': 'perm description',
            }],
        }],
    )
    url = f'{auth0_client.audience}/resource-servers/{auth0_client.api_id}'
    mocked.patch(url, status=200)
    url = f'{auth0_client.audience}/users/user_id/permissions'
    mocked.post(url, status=201)
    assert await auth0_client.set_user_permissions('user_id', ['permission'])


@pytest.mark.asyncio
async def test_delete_user_permissions(auth0_client, mocked):
    url = f'{auth0_client.audience}/users/user_id/permissions'
    call = functools.partial(
        auth0_client.delete_user_permissions,
        'user_id',
        ['permission'],
    )
    mocked.delete(url, status=204)
    assert await call()
    mocked.delete(url, status=400)
    with pytest.raises(Auth0Error):
        await call()


@pytest.mark.asyncio
async def test_get_api_permissions(auth0_client, mocked):
    url = f'{auth0_client.audience}/resource-servers?per_page=100'
    permissions = [{
        'value': 'perm-id',
        'description': 'perm description',
    }]
    mocked.get(
        url,
        status=200,
        payload=[{
            'identifier': auth0_client.api_id,
            'scopes': permissions,
        }],
    )
    assert (await auth0_client.get_api_permissions()) == permissions
    mocked.get(url, status=400)
    auth0_client._cache.pop(('api_permissions',), None)
    with pytest.raises(Auth0Error):
        await auth0_client.get_api_permissions()
    mocked.get(url, status=200, payload=[])
    with pytest.raises(Auth0Error):
        await auth0_client.get_api_permissions()
