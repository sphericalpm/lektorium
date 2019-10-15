import json
from graphql import GraphQLError
from six.moves.urllib.request import urlopen


class JWTMiddleware:
    def __init__(self, auth):
        self.auth = auth

    def resolve(self, next, root, info, **args):
        pass  # TODO: implement middleware logic here

    def get_token_auth(self, headers):
        """Obtains the Access Token from the Authorization Header
        """
        auth = headers.get("Authorization", None)
        if not auth:
            raise GraphExecutionError("Authorization header is expected", code=401)

        parts = auth.split()

        if parts[0].lower() != "bearer":
            raise GraphExecutionError("Authorization header must start with Bearer", code=401)

        elif len(parts) == 1:
            raise GraphExecutionError("Token not found", code=401)

        elif len(parts) > 2:
            raise GraphExecutionError("Authorization header must be Bearer token", code=401)

        splited_token = parts[1].split('.')
        token = '.'.join(splited_token[:3])

        return token

    def get_jwks(self):
        auth_domain = self.auth['data-auth0-domain']
        jsonurl = urlopen(f"https://{auth_domain}/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())

        return jwks


class GraphExecutionError(GraphQLError):
    def __init__(self, message, code=None, params=None):
        super().__init__(message)
        self.message = str(message)
        self.code = code
        self.params = params
