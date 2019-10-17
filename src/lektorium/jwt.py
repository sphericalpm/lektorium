import aiohttp
from graphql import GraphQLError
from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError


class JWTMiddleware:
    def __init__(self, auth):
        self.auth = auth

    async def resolve(self, next, root, info, **kwargs):
        if self.auth is None:
            raise AttributeError('auth should be not None')
        if all(self.auth.values()):
            token = self.get_token_auth(info.context['request'].headers)
            key = await self.public_key()
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

        if len(parts) == 1 or len(parts) > 2:
            raise GraphExecutionError('Authorization header must be Bearer token', code=401)

        elif parts[0].lower() != 'bearer':
            raise GraphExecutionError('Authorization header must start with Bearer', code=401)

        splited_token = parts[1].split('.')
        token = '.'.join(splited_token[:3])

        return token

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
        except JoseError as e:
            raise GraphExecutionError(f'Unable to decode token: {e.error}', code=401)
        else:
            return claims


class GraphExecutionError(GraphQLError):
    def __init__(self, message, code=None, params=None):
        super().__init__(message)
        self.message = str(message)
        self.code = code
        self.params = params
