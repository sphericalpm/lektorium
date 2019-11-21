import aiohttp


class AuthManagement:
    def __init__(self, domain, client_id, client_secret):
        self.url = f'https://{domain}/oauth/token'
        self.data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'audience': f'https://{domain}/api/v2/',
            'grant_type': 'client_credentials',
        }

    async def get_auth_token(self):
        async with aiohttp.ClientSession() as client:
            async with client.post(self.url, json=self.data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['access_token']

    def get_users(self):
        pass

    def get_user_permissions(self):
        pass
