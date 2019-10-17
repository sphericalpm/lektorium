import pytest
from lektorium.jwt import JWTMiddleware, GraphExecutionError


@pytest.fixture
def jwt_middleware():
    auth = {'data-auth0-domain': 'test.auth.com', 'data-auth0-id': 'test_id', 'data-auth0-api': 'test_api'}
    return JWTMiddleware(auth)


def test_get_token_auth(jwt_middleware):
    test_headers = {'Authorization': (
        'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZC'
        'I6IlJVWTJPRUZHUkVaQk16TTNORFk1TWpnd1FUSTVRemRETlVaR1JqZ3lOalZCUmtFd01UaENOdyJ9.eyJ'
        'uaWNrbmFtZSI6Im1qIiwibmFtZSI6Im1qQHNwaGVyaWNhbC5wbSIsInBpY3R1cmUiOiJodHRwczovL3MuZ'
        '3JhdmF0YXIuY29tL2F2YXRhci9hZjZmZGNiY2NiMjEwZTBmZjhmYjc3ZDkxMjYzMWQzNT9zPTQ4MCZyPXB'
        'nJmQ9aHR0cHMlM0ElMkYlMkZjZG4uYXV0aDAuY29tJTJGYXZhdGFycyUyRm1qLnBuZyIsInVwZGF0ZWRfY'
        'XQiOiIyMDE5LTEwLTE2VDE0OjEyOjIzLjYwN1oiLCJlbWFpbCI6Im1qQHNwaGVyaWNhbC5wbSIsImVtYWl'
        'sX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6Ly9hcC1sZWt0b3JpdW0uZXUuYXV0aDAuY29tLyIsI'
        'nN1YiI6ImF1dGgwfDVkN2I4N2ZiZTlkYWQ3MGRjYjI4YzQyZSIsImF1ZCI6Incxb3h2TXNGcFpDVzRHMjI'
        '0SThKUjdEMmV0OXlxVFlvIiwiaWF0IjoxNTcxMjk3ODIyLCJleHAiOjE1NzEzMzM4MjIsImF0X2hhc2giO'
        'iJoTXJ2RHdITmtFajFVRUp6SzQxNDFRIiwibm9uY2UiOiJQYmNiMFNRRks3aXRBWnVOUlp-TGhwOTlrMEJ'
        'Rc3R1cCJ9.Gwq8ECHeqBS9lYWyhGr8uR4bGQxzH8iu01XAepXY9fE1HEiFgFVq49ujGCxzRPkznKwaQhgt'
        'Xv13Vb8TMJ5H8gSpg6TXnnSk1LAg-gwLPawDA3eQacq6O391sPA2h14ISQouzOyrpD4YH9QFBtTWxCbLog'
        'pAYr29rBrqla8xekd64QiGHXYggJZ2eDpLEiQHfG3RfVrEBcayer3WbVVsb_Sb-3IsaITFF1e6ANKVs7GY'
        'oSIqUvUr_yh19mNUOEI7tHPAFjpZxbEtFAmrQThT7YAM1NO96RYn_HG6IJo6zWNyD-_1A92CkWAvT2z2fF'
        '6ycRMmnEtHNulExqNCm-e_MQ.eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IlJVWTJPRUZHU'
        'kVaQk16TTNORFk1TWpnd1FUSTVRemRETlVaR1JqZ3lOalZCUmtFd01UaENOdyJ9.eyJpc3MiOiJodHRwcz'
        'ovL2FwLWxla3Rvcml1bS5ldS5hdXRoMC5jb20vIiwic3ViIjoiYXV0aDB8NWQ3Yjg3ZmJlOWRhZDcwZGNi'
        'MjhjNDJlIiwiYXVkIjpbIkxla3Rvcml1bSIsImh0dHBzOi8vYXAtbGVrdG9yaXVtLmV1LmF1dGgwLmNvbS'
        '91c2VyaW5mbyJdLCJpYXQiOjE1NzEyOTc4MjIsImV4cCI6MTU3MTMwNTAyMiwiYXpwIjoidzFveHZNc0Zw'
        'WkNXNEcyMjRJOEpSN0QyZXQ5eXFUWW8iLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwicGVybW'
        'lzc2lvbnMiOltdfQ.kkfDbHLZT30RrK-X0IL3QCpVN4-ccp6C40ti4VQ_rJUrrAAzJwgxg-3SEfmvEppLl'
        'bWkOSsZgtIrPvJ_VqWxQte6a4MKF_bHlG4td04RSlln8N3uaeiyZfCeIIbXpdVzMfINRMwWKV0kJ9jjKVp'
        'gL5vhu_5j22EYqAgLQrPyt1Tx67Gm6msRe2WJYaKZMukM8-ZffOfjuOkrT99DEN-D-7zLQyH88LlS13YKp'
        'E3U6pScM4MRpMYNwdwsEN0KJZbkADvt3EToGmg_vGur8GnzNTF6t2Q3RXb3RWHpDJXPNKp5VDJ3hS09zqa'
        '6OWAMndioTWPzoDzcSNoSfdeipWJ7vA'
    )}
    test_token = (
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IlJVWTJPRUZHUkVaQk16TTNORFk1TWpnd1FUSTV'
        'RemRETlVaR1JqZ3lOalZCUmtFd01UaENOdyJ9.eyJuaWNrbmFtZSI6Im1qIiwibmFtZSI6Im1qQHNwaGVya'
        'WNhbC5wbSIsInBpY3R1cmUiOiJodHRwczovL3MuZ3JhdmF0YXIuY29tL2F2YXRhci9hZjZmZGNiY2NiMjEw'
        'ZTBmZjhmYjc3ZDkxMjYzMWQzNT9zPTQ4MCZyPXBnJmQ9aHR0cHMlM0ElMkYlMkZjZG4uYXV0aDAuY29tJTJ'
        'GYXZhdGFycyUyRm1qLnBuZyIsInVwZGF0ZWRfYXQiOiIyMDE5LTEwLTE2VDE0OjEyOjIzLjYwN1oiLCJlbW'
        'FpbCI6Im1qQHNwaGVyaWNhbC5wbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6Ly9hc'
        'C1sZWt0b3JpdW0uZXUuYXV0aDAuY29tLyIsInN1YiI6ImF1dGgwfDVkN2I4N2ZiZTlkYWQ3MGRjYjI4YzQy'
        'ZSIsImF1ZCI6Incxb3h2TXNGcFpDVzRHMjI0SThKUjdEMmV0OXlxVFlvIiwiaWF0IjoxNTcxMjk3ODIyLCJ'
        'leHAiOjE1NzEzMzM4MjIsImF0X2hhc2giOiJoTXJ2RHdITmtFajFVRUp6SzQxNDFRIiwibm9uY2UiOiJQYm'
        'NiMFNRRks3aXRBWnVOUlp-TGhwOTlrMEJRc3R1cCJ9.Gwq8ECHeqBS9lYWyhGr8uR4bGQxzH8iu01XAepXY'
        '9fE1HEiFgFVq49ujGCxzRPkznKwaQhgtXv13Vb8TMJ5H8gSpg6TXnnSk1LAg-gwLPawDA3eQacq6O391sPA'
        '2h14ISQouzOyrpD4YH9QFBtTWxCbLogpAYr29rBrqla8xekd64QiGHXYggJZ2eDpLEiQHfG3RfVrEBcayer'
        '3WbVVsb_Sb-3IsaITFF1e6ANKVs7GYoSIqUvUr_yh19mNUOEI7tHPAFjpZxbEtFAmrQThT7YAM1NO96RYn_'
        'HG6IJo6zWNyD-_1A92CkWAvT2z2fF6ycRMmnEtHNulExqNCm-e_MQ'
    )
    assert jwt_middleware.get_token_auth(test_headers) == test_token

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth({})
    assert 'Authorization header is expected' == str(excinfo.value)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth(dict(Authorization='token testtoken'))
    assert 'Authorization header must start with Bearer' == str(excinfo.value)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth(dict(Authorization='testtoken'))
    assert 'Authorization header must be Bearer token' == str(excinfo.value)

    with pytest.raises(GraphExecutionError) as excinfo:
        jwt_middleware.get_token_auth(dict(Authorization='token token token'))
    assert 'Authorization header must be Bearer token' == str(excinfo.value)
