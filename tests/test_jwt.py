import json
from collections import namedtuple

import pytest

from lektorium.jwt import GraphExecutionError, JWTMiddleware


TEST_TOKEN = (
    'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuaWNrbmFtZSI6Ik1heCBKZWtvdiIsI'
    'mVtYWlsIjoibWpAbWFpbC5tZSIsImlhdCI6MTUxNjIzOTAyMn0.BfvCagmp3uLgjMCWqFQ'
    '7E85rcajlDSO7RTMaiGH2aQ4VyC573Cu3Wrvs6yq6xwBK0UqIFDL569pMIkrDFsJWROoEA'
    '6idJPSMwxCNXBK-lXcCoakGznX6fJ6S-7JF6mqF4An3hWx6XcX61Ck5j-ARBBq12FE_nr8'
    'WQ9wFcwXWc6MOrzCcFGbY_SsSk5mVruQ9Wm3qZRza8DIAIJLJR9Kmuz6NnIqCw5aXVtDC3'
    'f3FXWvG_W67CvEFiq-XoCAZPXnKoMFUqx-CAMaV5wPWKaMJxiA9iynksam-A5pimthDepS'
    'FSVpulSoIyYmCAaIOLA0QKRWhHz3Ef8fGXBcpS1FwIQ'
)

TEST_HEADERS = {'Authorization': f'Bearer {TEST_TOKEN}.{TEST_TOKEN}'}

TEST_JWK = {
    "kty": "RSA",
    "e": "AQAB",
    "n": (
        'nzyis1ZjfNB0bBgKFMSvvkTtwlvBsaJq7S5wA-kzeVOVpVWwkWdVha4s38XM_pa_yr47'
        'av7-z3VTmvDRyAHcaT92whREFpLv9cj5lTeJSibyr_Mrm_YtjCZVWgaOYIhwrXwKLqPr'
        '_11inWsAkfIytvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47'
        'XUu0t8Y0e-lf4s4OxQawWD79J9_5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMq'
        'tvWbV6L11BWkpzGXSW4Hv43qa-GSYOD2QU68Mb59oSk2OB-BtOLpJofmbGEGgvmwyCI9'
        'Mw'
    ),
}


@pytest.fixture
def jwt_middleware():
    return JWTMiddleware('test.auth0.com')


def test_get_token_auth(jwt_middleware):
    assert jwt_middleware.get_token_auth(TEST_HEADERS) == (TEST_TOKEN, TEST_TOKEN)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth({})
    assert 'Authorization header is expected' == str(excinfo.value)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth(dict(Authorization='token testtoken'))
    assert 'Authorization header must be Bearer token' == str(excinfo.value)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth(dict(Authorization='testtoken'))
    assert 'Authorization header must be Bearer token' == str(excinfo.value)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth(dict(Authorization='token token token'))
    assert 'Authorization header must be Bearer token' == str(excinfo.value)


def test_decode_token(jwt_middleware):
    token = jwt_middleware.decode_token(TEST_TOKEN, TEST_JWK)
    assert token['nickname'] == 'Max Jekov'
    with pytest.raises(GraphExecutionError):
        jwt_middleware.decode_token('', TEST_JWK)
    with pytest.raises(ValueError):
        jwt_middleware.decode_token(TEST_TOKEN, '')


def test_jwt_middleware_init():
    with pytest.raises(ValueError):
        JWTMiddleware(None)
    with pytest.raises(ValueError):
        JWTMiddleware('')
    with pytest.raises(ValueError):
        JWTMiddleware('aaa.bbb.com')


@pytest.mark.asyncio
async def test_public_key(aresponses, jwt_middleware):
    def response_handler(request):
        return aresponses.Response(
            status=200,
            headers={'Content-Type': 'application/json'},
            body=b'{"public_key": "somekey"}'
        )
    aresponses.add(
        jwt_middleware.auth0_domain,
        '/.well-known/jwks.json',
        'get',
        response_handler
    )
    key = await jwt_middleware.public_key
    assert key == {'public_key': 'somekey'}


def test_m(monkeypatch):
    Info = namedtuple('Info', 'context')
    Request = namedtuple('Request', 'headers')
    info = Info({'request': Request(TEST_HEADERS)})
    assert info.context['request'].headers == TEST_HEADERS


@pytest.mark.asyncio
async def test_jwt_resolve(aresponses, jwt_middleware, monkeypatch):
    Info = namedtuple('Info', 'context')
    Request = namedtuple('Request', 'headers')
    info = Info({'request': Request(TEST_HEADERS)})

    def test_next(root, info, **kwargs):
        return info

    def response_handler(request):
        return aresponses.Response(
            status=200,
            headers={'Content-Type': 'application/json'},
            body=bytes(json.dumps(TEST_JWK), encoding='utf-8')
        )

    aresponses.add(
        jwt_middleware.auth0_domain,
        '/.well-known/jwks.json',
        'get',
        response_handler
    )
    resolve = await jwt_middleware.resolve(test_next, None, info)
    assert resolve.context['userdata'] == ('Max Jekov', 'mj@mail.me')
