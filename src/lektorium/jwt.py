import aiohttp
from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from cached_property import cached_property
from graphql import GraphQLError


class JWTMiddleware:
    def __init__(self, auth0_domain):
        if not (auth0_domain and auth0_domain.endswith('.auth0.com')):
            raise ValueError('wrong auth0 domain')
        self.auth0_domain = auth0_domain

    async def resolve(self, next, root, info, **kwargs):
        userdata, permissions = await self.info(info.context['request'])
        if userdata is not None:
            info.context['userdata'] = userdata
        info.context['user_permissions'] = permissions
        return next(root, info, **kwargs)

    async def info(self, request):
        token, extra = self.get_token_auth(request.headers)
        key = await self.public_key
        payload = self.decode_token(token, key)
        permissions = self.decode_token(extra, key).get('permissions', [])
        userdata = None
        if payload:
            userdata = (payload['nickname'], payload['email'])
        return userdata, permissions

    def get_token_auth(self, headers):
        """Obtains the Access Token from the Authorization Header"""
        auth = headers.get('Authorization', None)
        if auth is None:
            raise GraphExecutionError(
                'Authorization header is expected',
                code=401,
            )

        parts = auth.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise GraphExecutionError(
                'Authorization header must be Bearer token',
                code=401,
            )

        split = parts[1].split('.')
        token = '.'.join(split[:3])
        extra = '.'.join(split[3:])

        return token, extra

    @cached_property
    async def public_key(self):
        async with aiohttp.ClientSession() as client:
            jwks_url = f'https://{self.auth0_domain}/.well-known/jwks.json'
            async with client.get(jwks_url) as resp:
                return await resp.json()

    def decode_token(self, token, key):
        jwt = JsonWebToken(['RS256'])
        try:
            claims = jwt.decode(token, key)
            claims.validate()
            return claims
        except JoseError as e:
            raise GraphExecutionError(
                f'Unable to decode token: {e.error}',
                code=401,
            )


class GraphExecutionError(GraphQLError):
    def __init__(self, message, code=None, params=None):
        super().__init__(message)
        self.message = str(message)
        self.code = code
        self.params = params
