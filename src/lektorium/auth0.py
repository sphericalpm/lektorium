import aiohttp
import asyncio
import time
from aiohttp import ClientSession


class FakeAuth0Client:
    def __init__(self):
        self.token = 'test_token'
        self.users = [
            {'user_id': 'test_id', 'name': 'Max Jekov', 'nickname': 'mj', 'email': 'mj@mail.m'}
        ]
        self.users_permissions = {
            'test_id': [{'permission_name': 'Test Permission1', 'description': ''}]
        }
        self.api_permissions = [
            {'value': 'Test Permission1', 'description': ''},
            {'value': 'Test Permission2', 'description': ''},
        ]

    @property
    async def auth_token(self):
        return self.token

    async def get_users(self):
        for user in self.users:
            permissions = self.users_permissions.get(user['user_id'])
            user['permissions'] = [permission['permission_name'] for permission in permissions]
        return self.users

    async def get_user_permissions(self, user_id):
        result = self.users_permissions.get(user_id)
        if result is None:
            raise Auth0Error()
        return result

    async def set_user_permissions(self, user_id, permissions):
        if user_id in self.users_permissions:
            new_permissions = [
                {'permission_name': name, 'description': ''} for name in permissions
            ]
            for permission in new_permissions:
                if permission not in self.users_permissions[user_id]:
                    self.users_permissions[user_id].append(permission)
            return True
        raise Auth0Error

    async def delete_user_permissions(self, user_id, permissions):
        if user_id in self.users_permissions:
            permissions_to_delete = [
                {'permission_name': name, 'description': ''} for name in permissions
            ]
            for index, permission in enumerate(self.users_permissions[user_id]):
                if permission in permissions_to_delete:
                    del self.users_permissions[user_id][index]
            return True
        raise Auth0Error

    async def get_api_permissions(self):
        return self.api_permissions


class ThrottledClientSession(ClientSession):
    def __init__(self, *args, **kwargs):
        self.last_request_time = time.time()
        self.delay = 1
        super().__init__(*args, **kwargs)

    async def _request(self, *args, **kwargs):
        lock = asyncio.Lock()
        with lock:
            await asyncio.sleep(self.last_request_time + self.delay - time.time())
            self.last_request_time = time.time()
            return await super()._request(*args, **kwargs)


class Auth0Client:
    def __init__(self, auth):
        self.throttled_session = ThrottledClientSession()
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
        async with ClientSession() as client:
            async with client.post(self.url, json=self.data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result['access_token']
                else:
                    result = await resp.json()
                    raise Auth0Error(f'Error {resp.status}')

    async def get_users(self):
        auth_token = await self.auth_token
        headers = {'Authorization': 'Bearer {0}'.format(auth_token)}
        async with aiohttp.ClientSession(headers=headers) as client:
            url = self.data["audience"] + 'users'
            params = {'fields': 'name,nickname,email,user_id'}
            async with client.get(url, params=params) as resp:
                if resp.status == 200:
                    users = await resp.json()
                    for user in users:
                        if user.get('user_id'):
                            permissions = await self.get_user_permissions(user['user_id'])
                            user['permissions'] = [permission['permission_name'] for permission in permissions]
                    return users
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
