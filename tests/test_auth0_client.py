import pytest
from aioresponses import aioresponses
from lektorium.auth0 import Auth0Client, Auth0Error

pytestmark = pytest.mark.asyncio

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


async def test_auth_token(auth0_client):
    with aioresponses() as mocked:
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        resp = await auth0_client.auth_token
        assert resp == 'test_token'
        mocked.post(auth0_client.url, status=404)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.auth_token


async def test_get_users(auth0_client):
    with aioresponses() as mocked:
        url = auth0_client.data["audience"] + 'users?fields=name,nickname,email,user_id'
        users_response = [{'username': 'mjekov'}]
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.get(url, status=200, payload=users_response)
        resp = await auth0_client.get_users()
        assert resp == users_response
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.get(url, status=400)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.get_users()


async def test_get_user_permissions(auth0_client):
    with aioresponses() as mocked:
        url = auth0_client.data["audience"] + 'users/user_id/permissions'
        permissions_response = [{'permission_name': 'read:projects'}]
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.get(url, status=200, payload=permissions_response)
        resp = await auth0_client.get_user_permissions('user_id')
        assert resp == permissions_response
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.get(url, status=400)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.get_user_permissions('user_id')


async def test_set_user_permissions(auth0_client):
    with aioresponses() as mocked:
        url = auth0_client.data["audience"] + 'users/user_id/permissions'
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.post(url, status=201)
        resp = await auth0_client.set_user_permissions('user_id', ['permission'])
        assert resp
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.post(url, status=400)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.set_user_permissions('user_id', ['permission'])


async def test_delete_user_permissions(auth0_client):
    with aioresponses() as mocked:
        url = auth0_client.data["audience"] + 'users/user_id/permissions'
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.delete(url, status=204)
        resp = await auth0_client.delete_user_permissions('user_id', ['permission'])
        assert resp
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.delete(url, status=400)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.delete_user_permissions('user_id', ['permission'])


async def test_get_api_permissions(auth0_client):
    with aioresponses() as mocked:
        url = auth0_client.data["audience"] + 'resource-servers'
        permissions_response = [{'identifier': auth0_client.api_id, 'scopes': 'testdata'}]
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.get(url, status=200, payload=permissions_response)
        resp = await auth0_client.get_api_permissions()
        assert resp == 'testdata'
        mocked.post(auth0_client.url, status=200, payload=TEST_TOKEN)
        mocked.get(url, status=400)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.get_api_permissions()
