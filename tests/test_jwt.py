import pytest
import aiohttp
import aresponses
from lektorium.jwt import JWTMiddleware, GraphExecutionError


@pytest.fixture
def jwt_middleware():
    auth = {
        'data-auth0-domain': 'test.auth.com',
        'data-auth0-id': 'test_id',
        'data-auth0-api': 'test_api',
    }
    return JWTMiddleware(auth)


def test_get_token_auth(jwt_middleware):
    test_headers = {'Authorization': (
        'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IlJVWTJPRUZHUkVaQk'
        '16TTNORFk1TWpnd1FUSTVRemRETlVaR1JqZ3lOalZCUmtFd01UaENOdyJ9.eyJuaWNrbm'
        'FtZSI6Im1qIiwibmFtZSI6Im1qQHNwaGVyaWNhbC5wbSIsInBpY3R1cmUiOiJodHRwczo'
        'vL3MuZ3JhdmF0YXIuY29tL2F2YXRhci9hZjZmZGNiY2NiMjEwZTBmZjhmYjc3ZDkxMjYz'
        'MWQzNT9zPTQ4MCZyPXBnJmQ9aHR0cHMlM0ElMkYlMkZjZG4uYXV0aDAuY29tJTJGYXZhd'
        'GFycyUyRm1qLnBuZyIsInVwZGF0ZWRfYXQiOiIyMDE5LTEwLTE2VDE0OjEyOjIzLjYwN1'
        'oiLCJlbWFpbCI6Im1qQHNwaGVyaWNhbC5wbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSw'
        'iaXNzIjoiaHR0cHM6Ly9hcC1sZWt0b3JpdW0uZXUuYXV0aDAuY29tLyIsInN1YiI6ImF1'
        'dGgwfDVkN2I4N2ZiZTlkYWQ3MGRjYjI4YzQyZSIsImF1ZCI6Incxb3h2TXNGcFpDVzRHM'
        'jI0SThKUjdEMmV0OXlxVFlvIiwiaWF0IjoxNTcxMjk3ODIyLCJleHAiOjE1NzEzMzM4Mj'
        'IsImF0X2hhc2giOiJoTXJ2RHdITmtFajFVRUp6SzQxNDFRIiwibm9uY2UiOiJQYmNiMFN'
        'RRks3aXRBWnVOUlp-TGhwOTlrMEJRc3R1cCJ9.Gwq8ECHeqBS9lYWyhGr8uR4bGQxzH8i'
        'u01XAepXY9fE1HEiFgFVq49ujGCxzRPkznKwaQhgtXv13Vb8TMJ5H8gSpg6TXnnSk1LAg'
        '-gwLPawDA3eQacq6O391sPA2h14ISQouzOyrpD4YH9QFBtTWxCbLogpAYr29rBrqla8xe'
        'kd64QiGHXYggJZ2eDpLEiQHfG3RfVrEBcayer3WbVVsb_Sb-3IsaITFF1e6ANKVs7GYoS'
        'IqUvUr_yh19mNUOEI7tHPAFjpZxbEtFAmrQThT7YAM1NO96RYn_HG6IJo6zWNyD-_1A92'
        'CkWAvT2z2fF6ycRMmnEtHNulExqNCm-e_MQ.eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1N'
        'iIsImtpZCI6IlJVWTJPRUZHUkVaQk16TTNORFk1TWpnd1FUSTVRemRETlVaR1JqZ3lOal'
        'ZCUmtFd01UaENOdyJ9.eyJpc3MiOiJodHRwczovL2FwLWxla3Rvcml1bS5ldS5hdXRoMC'
        '5jb20vIiwic3ViIjoiYXV0aDB8NWQ3Yjg3ZmJlOWRhZDcwZGNiMjhjNDJlIiwiYXVkIjp'
        'bIkxla3Rvcml1bSIsImh0dHBzOi8vYXAtbGVrdG9yaXVtLmV1LmF1dGgwLmNvbS91c2Vy'
        'aW5mbyJdLCJpYXQiOjE1NzEyOTc4MjIsImV4cCI6MTU3MTMwNTAyMiwiYXpwIjoidzFve'
        'HZNc0ZwWkNXNEcyMjRJOEpSN0QyZXQ5eXFUWW8iLCJzY29wZSI6Im9wZW5pZCBwcm9maW'
        'xlIGVtYWlsIiwicGVybWlzc2lvbnMiOltdfQ.kkfDbHLZT30RrK-X0IL3QCpVN4-ccp6C'
        '40ti4VQ_rJUrrAAzJwgxg-3SEfmvEppLlbWkOSsZgtIrPvJ_VqWxQte6a4MKF_bHlG4td'
        '04RSlln8N3uaeiyZfCeIIbXpdVzMfINRMwWKV0kJ9jjKVpgL5vhu_5j22EYqAgLQrPyt1'
        'Tx67Gm6msRe2WJYaKZMukM8-ZffOfjuOkrT99DEN-D-7zLQyH88LlS13YKpE3U6pScM4M'
        'RpMYNwdwsEN0KJZbkADvt3EToGmg_vGur8GnzNTF6t2Q3RXb3RWHpDJXPNKp5VDJ3hS09'
        'zqa6OWAMndioTWPzoDzcSNoSfdeipWJ7vA'
    )}
    test_token = (
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IlJVWTJPRUZHUkVaQk16TTNOR'
        'Fk1TWpnd1FUSTVRemRETlVaR1JqZ3lOalZCUmtFd01UaENOdyJ9.eyJuaWNrbmFtZSI6I'
        'm1qIiwibmFtZSI6Im1qQHNwaGVyaWNhbC5wbSIsInBpY3R1cmUiOiJodHRwczovL3MuZ3'
        'JhdmF0YXIuY29tL2F2YXRhci9hZjZmZGNiY2NiMjEwZTBmZjhmYjc3ZDkxMjYzMWQzNT9'
        'zPTQ4MCZyPXBnJmQ9aHR0cHMlM0ElMkYlMkZjZG4uYXV0aDAuY29tJTJGYXZhdGFycyUy'
        'Rm1qLnBuZyIsInVwZGF0ZWRfYXQiOiIyMDE5LTEwLTE2VDE0OjEyOjIzLjYwN1oiLCJlb'
        'WFpbCI6Im1qQHNwaGVyaWNhbC5wbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIj'
        'oiaHR0cHM6Ly9hcC1sZWt0b3JpdW0uZXUuYXV0aDAuY29tLyIsInN1YiI6ImF1dGgwfDV'
        'kN2I4N2ZiZTlkYWQ3MGRjYjI4YzQyZSIsImF1ZCI6Incxb3h2TXNGcFpDVzRHMjI0SThK'
        'UjdEMmV0OXlxVFlvIiwiaWF0IjoxNTcxMjk3ODIyLCJleHAiOjE1NzEzMzM4MjIsImF0X'
        '2hhc2giOiJoTXJ2RHdITmtFajFVRUp6SzQxNDFRIiwibm9uY2UiOiJQYmNiMFNRRks3aX'
        'RBWnVOUlp-TGhwOTlrMEJRc3R1cCJ9.Gwq8ECHeqBS9lYWyhGr8uR4bGQxzH8iu01XAep'
        'XY9fE1HEiFgFVq49ujGCxzRPkznKwaQhgtXv13Vb8TMJ5H8gSpg6TXnnSk1LAg-gwLPaw'
        'DA3eQacq6O391sPA2h14ISQouzOyrpD4YH9QFBtTWxCbLogpAYr29rBrqla8xekd64QiG'
        'HXYggJZ2eDpLEiQHfG3RfVrEBcayer3WbVVsb_Sb-3IsaITFF1e6ANKVs7GYoSIqUvUr_'
        'yh19mNUOEI7tHPAFjpZxbEtFAmrQThT7YAM1NO96RYn_HG6IJo6zWNyD-_1A92CkWAvT2'
        'z2fF6ycRMmnEtHNulExqNCm-e_MQ'
    )
    assert jwt_middleware.get_token_auth(test_headers) == test_token

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
    test_token = (
        'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiSm9obiBEb2UifQ.FL7fo'
        'y7kV9SVoC6GLEqwatuYz39BWoEUpZ9sv00zg2oJneJFkwPYYBCj92xu0Fry7zqLRkhFev'
        'eUKtSgZV6AinDvdWWH9Is8ku3l871ut-ECiR8-Co7qdIbQet3IhiLggHko4Z9Ez7F-pWm'
        'ppV7BRJmYdFjbrurLfgN191VE9xC8AmnzSIPTFczg9g_aycqhea4ncd9YjiGV2QlmNB4q'
        '1aCZ3V7QyO4KwJnnLeI4tykXjNRVXfPuInaE_f0TpzpRbzJelAGhL5cmO_b0kJswCEqon'
        'YMvsVdGqM9jxWMebs7L2k2s2nZ3MQNo-gVIv3E2GfaBpCgGxO-8kyh8sBal3A'
    )
    test_key = (
        '-----BEGIN PUBLIC KEY-----\n'
        'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnzyis1ZjfNB0bBgKFMSv'
        'vkTtwlvBsaJq7S5wA+kzeVOVpVWwkWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHc'
        'aT92whREFpLv9cj5lTeJSibyr/Mrm/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIy'
        'tvHWTxZYEcXLgAXFuUuaS3uF9gEiNQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0'
        'e+lf4s4OxQawWD79J9/5d3Ry0vbV3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWb'
        'V6L11BWkpzGXSW4Hv43qa+GSYOD2QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9'
        'MwIDAQAB\n'
        '-----END PUBLIC KEY-----'
    )
    token = jwt_middleware.decode_token(test_token, test_key)
    assert token == {'name': 'John Doe'}
    with pytest.raises(GraphExecutionError):
        jwt_middleware.decode_token('', test_key)
    with pytest.raises(ValueError):
        jwt_middleware.decode_token(test_token, '')


@pytest.mark.asyncio
async def test_public_key(jwt_middleware):
    pass


@pytest.mark.asyncio
async def test_middleware(jwt_middleware):
    pass
