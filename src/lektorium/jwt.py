import json
from graphql import GraphQLError
from six.moves.urllib.request import urlopen
from authlib.jose import JsonWebToken, jwk
from cached_property import cached_property


class JWTMiddleware:
    def __init__(self, auth):
        self.auth = auth

    def resolve(self, next, root, info, **kwargs):
        if not all(self.auth.values()):
            return next(root, info, **kwargs)
        token = self.get_token_auth(info.context['request'].headers)
        key = self.public_key
        payload = self.decode_token(token, key)
        if payload:
            userdata = (payload['nickname'], payload['email'])
            info.context['userdata'] = userdata
            return next(root, info, **kwargs)

    def get_token_auth(self, headers):
        """Obtains the Access Token from the Authorization Header
        """
        auth = headers.get('Authorization', None)
        if not auth:
            raise GraphExecutionError('Authorization header is expected', code=401)

        parts = auth.split()

        if parts[0].lower() != 'bearer':
            raise GraphExecutionError('Authorization header must start with Bearer', code=401)

        elif len(parts) == 1:
            raise GraphExecutionError('Token not found', code=401)

        elif len(parts) > 2:
            raise GraphExecutionError('Authorization header must be Bearer token', code=401)

        splited_token = parts[1].split('.')
        token = '.'.join(splited_token[:3])

        return token

    @cached_property
    def public_key(self):
        auth_domain = self.auth['data-auth0-domain']
        jsonurl = urlopen(f'https://{auth_domain}/.well-known/jwks.json')
        jwks = json.loads(jsonurl.read())
        key = jwk.loads(jwks['keys'][0])

        return key

    def decode_token(self, token, key):
        jwt = JsonWebToken(['RS256'])
        try:
            claims = jwt.decode(token, key)
            claims.validate()
        except Exception:
            raise GraphExecutionError('Unable to decode token', code=401)
        else:
            return claims


class GraphExecutionError(GraphQLError):
    def __init__(self, message, code=None, params=None):
        super().__init__(message)
        self.message = str(message)
        self.code = code
        self.params = params
