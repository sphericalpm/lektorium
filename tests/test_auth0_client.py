import pytest
from aioresponses import aioresponses
from lektorium.auth0 import Auth0Client, Auth0Error

pytestmark = pytest.mark.asyncio


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
    test_token = {'access_token': 'test_token'}
    with aioresponses() as mocked:
        mocked.post(auth0_client.url, status=200, payload=test_token)
        resp = await auth0_client.auth_token
        assert resp == 'test_token'
        mocked.post(auth0_client.url, status=404)
        with pytest.raises(Auth0Error):
            resp = await auth0_client.auth_token
