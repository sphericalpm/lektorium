import aiohttp


class Auth0Client:
    def __init__(self, domain, client_id, client_secret):
        self.url = f'https://{domain}/oauth/token'
        self.data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': f'https://{domain}/api/v2/',
            'grant_type': 'client_credentials',
        }

    @property
    async def auth_token(self):
        async with aiohttp.ClientSession() as client:
            async with client.post(self.url, json=self.data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['access_token']

    async def get_users(self):
        auth_token = await self.auth_token
        headers = {"Authorization": "Bearer {0}".format(auth_token)}
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data["audience"] + 'users'
            async with client.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()

    async def get_user_permissions(self, user_id):
        auth_token = await self.auth_token
        headers = {"Authorization": "Bearer {0}".format(auth_token)}
        async with aiohttp.ClientSession(headers=headers) as client:
            url = "{0}users/{1}/permissions".format(self.data['audience'],user_id)
            async with client.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
