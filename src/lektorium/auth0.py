import aiohttp


class Auth0Client:
    def __init__(self, auth):
        self.url = 'https://{0}/oauth/token'.format(auth['data-auth0-domain'])
        self.api_id = auth['data-auth0-api']
        self.data = {
            'client_id': auth['data-auth0-management-id'],
            'client_secret': auth['data-auth0-management-secret'],
            'audience': 'https://{0}/api/v2/'.format(auth['data-auth0-domain']),
            'grant_type': 'client_credentials',
        }

    @property
    async def auth_token(self):
        async with aiohttp.ClientSession() as client:
            async with client.post(self.url, json=self.data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['access_token']
                else:
                    result = await resp.json()
                    raise Auth0Error('{0}, {1}'.format(result['error'], result['error_description']))

    async def get_users(self):
        auth_token = await self.auth_token
        headers = {'Authorization': 'Bearer {0}'.format(auth_token)}
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data["audience"] + 'users'
            async with client.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Auth0Error(f'Error {resp.status}')

    async def get_user_permissions(self, user_id):
        auth_token = await self.auth_token
        headers = {'Authorization': 'Bearer {0}'.format(auth_token)}
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data['audience'] + f'users/{user_id}/permissions'
            async with client.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Auth0Error(f'Error {resp.status}')

    async def set_user_permissions(self, user_id, permissions):
        auth_token = await self.auth_token
        headers = {'Authorization': 'Bearer {0}'.format(auth_token)}
        data = {'permissions': []}
        for permission in permissions:
            data['permissions'].append({'resource_server_identifier': self.api_id, 'permission_name': permission})
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data['audience'] + f'users/{user_id}/permissions'
            async with client.post(url, json=data) as resp:
                if resp.status == 201:
                    return True
                else:
                    raise Auth0Error(f'Error {resp.status}')

    async def delete_user_permissions(self, user_id, permissions):
        auth_token = await self.auth_token
        headers = {'Authorization': 'Bearer {0}'.format(auth_token)}
        data = {'permissions': []}
        for permission in permissions:
            data['permissions'].append({'resource_server_identifier': self.api_id, 'permission_name': permission})
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data['audience'] + f'users/{user_id}/permissions'
            async with client.delete(url, json=data) as resp:
                if resp.status == 204:
                    return True
                else:
                    raise Auth0Error(f'Error {resp.status}')

    async def get_api_permissions(self):
        auth_token = await self.auth_token
        headers = {'Authorization': 'Bearer {0}'.format(auth_token)}
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data['audience'] + 'resource-servers'
            async with client.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    data = list(filter(lambda x: x.get('identifier') == self.api_id, data))
                    if data:
                        result = data[0]['scopes']
                        return result
                    else:
                        raise Auth0Error(f"'{self.api_id}' api was not found")
                else:
                    raise Auth0Error(f'Error {resp.status}')


class Auth0Error(Exception):
    pass