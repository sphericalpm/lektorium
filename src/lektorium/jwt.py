import aiohttp
from graphql import GraphQLError
from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from cached_property import cached_property


class JWTMiddleware:
    def __init__(self, auth):
        if auth is None:
            raise AttributeError('auth should be not None')
        if all(auth.values()) and len(auth.values()) == 3:
            self.auth = auth
        else:
            raise ValueError('Check auth0 params')

    async def resolve(self, next, root, info, **kwargs):
        token = self.get_token_auth(info.context['request'].headers)
        key = await self.public_key
        payload = self.decode_token(token, key)
        if payload:
            userdata = (payload['nickname'], payload['email'])
            info.context['userdata'] = userdata
        return next(root, info, **kwargs)

    def get_token_auth(self, headers):
        """Obtains the Access Token from the Authorization Header
        """
        auth = headers.get('Authorization', None)
        if auth is None:
            raise GraphExecutionError('Authorization header is expected', code=401)

        parts = auth.split()

        if len(parts) == 1 or len(parts) > 2 or parts[0].lower() != 'bearer':
            raise GraphExecutionError('Authorization header must be Bearer token', code=401)

        token = '.'.join(parts[1].split('.')[:3])

        return token

    @cached_property
    async def public_key(self):
        auth_domain = self.auth['data-auth0-domain']
        async with aiohttp.ClientSession() as client:
            async with client.get(f'https://{auth_domain}/.well-known/jwks.json') as resp:
                return await resp.json()

    def decode_token(self, token, key):
        jwt = JsonWebToken(['RS256'])
        try:
            claims = jwt.decode(token, key)
            claims.validate()
            return claims
        except JoseError as e:
            raise GraphExecutionError(f'Unable to decode token: {e.error}', code=401)


class GraphExecutionError(GraphQLError):
    def __init__(self, message, code=None, params=None):
        super().__init__(message)
        self.message = str(message)
        self.code = code
        self.params = params
