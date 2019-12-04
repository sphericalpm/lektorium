import asyncio
import time

import wrapt
from aiohttp import ClientSession


def cacher(method_alias):
    @wrapt.decorator
    async def wrapper(wrapped, instance, args, kwargs):
        if kwargs:
            raise Exception('Cannot use keyword args')
        key = (method_alias, *args)
        if key not in instance._cache:
            instance._cache.update({key: await wrapped(*args)})
        return instance._cache[key]
    return wrapper


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
    DELAY = 0.6

    def __init__(self, *args, **kwargs):
        self.last_request_time = time.time()
        self.lock = asyncio.Lock()
        super().__init__(*args, **kwargs)

    async def _request(self, *args, **kwargs):
        async with self.lock:
            sleep_time = self.last_request_time + self.DELAY - time.time()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self.last_request_time = time.time()
            return await super()._request(*args, **kwargs)


class Auth0Client:
    CACHE_VALID_PERIOD = 60

    def __init__(self, auth):
        self._cache = dict()
        self.session = ThrottledClientSession()
        self.url = 'https://{0}/oauth/token'.format(auth['data-auth0-domain'])
        self.api_id = auth['data-auth0-api']
        self.data = {
            'client_id': auth['data-auth0-management-id'],
            'client_secret': auth['data-auth0-management-secret'],
            'audience': 'https://{0}/api/v2/'.format(auth['data-auth0-domain']),
            'grant_type': 'client_credentials',
        }
        self.token = None
        self.token_time = time.time() + self.CACHE_VALID_PERIOD

    @property
    async def auth_token(self):
        if self.token is not None:
            if time.time() - self.token_time < self.CACHE_VALID_PERIOD:
                return self.token
        async with self.session.post(self.url, json=self.data) as resp:
            resp_status = resp.status
            if resp_status != 200:
                self.token = None
                raise Auth0Error(f'Error {resp_status}')
            result = await resp.json()
            self.token = result['access_token']
        self.token_time = time.time()
        return self.token

    @property
    async def auth_headers(self):
        headers = {'Authorization': 'Bearer {0}'.format(await self.auth_token)}
        return headers

    @cacher('users')
    async def get_users(self):
        url = self.data["audience"] + 'users'
        params = {'fields': 'name,nickname,email,user_id'}
        async with self.session.get(url, params=params, headers=await self.auth_headers) as resp:
            if resp.status == 200:
                users = await resp.json()
                for user in users:
                    if user.get('user_id'):
                        permissions = await self.get_user_permissions(user['user_id'])
                        user['permissions'] = [permission['permission_name'] for permission in permissions]
                return users
            else:
                raise Auth0Error(f'Error {resp.status}')

    @cacher('user_permissions')
    async def get_user_permissions(self, user_id):
        url = self.data['audience'] + f'users/{user_id}/permissions'
        async with self.session.get(url, headers=await self.auth_headers) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                raise Auth0Error(f'Error {resp.status}')

    async def set_user_permissions(self, user_id, permissions):
        data = {'permissions': []}
        for permission in permissions:
            data['permissions'].append({'resource_server_identifier': self.api_id, 'permission_name': permission})
        url = self.data['audience'] + f'users/{user_id}/permissions'
        async with self.session.post(url, json=data, headers=await self.auth_headers) as resp:
            if resp.status != 201:
                raise Auth0Error(f'Error {resp.status}')
            self._cache.pop(('users',), None)
            self._cache.pop(('user_permissions', user_id), None)
            return True

    async def delete_user_permissions(self, user_id, permissions):
        self._cache.clear()
        data = {'permissions': []}
        for permission in permissions:
            data['permissions'].append({'resource_server_identifier': self.api_id, 'permission_name': permission})
        url = self.data['audience'] + f'users/{user_id}/permissions'
        async with self.session.delete(url, json=data, headers=await self.auth_headers) as resp:
            if resp.status != 204:
                raise Auth0Error(f'Error {resp.status}')
            self._cache.pop(('users',), None)
            self._cache.pop(('user_permissions', user_id), None)
            return True

    @cacher('api_permissions')
    async def get_api_permissions(self):
        url = self.data['audience'] + 'resource-servers'
        async with self.session.get(url, headers=await self.auth_headers) as resp:
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

    async def add_api_permission(self, permission_name, description):
        data = await self.get_api_permissions()
        data.append({'value': permission_name, 'description': description})
        data = {'scopes': data}
        url = self.data['audience'] + 'resource-servers/' + self.api_id
        async with self.session.patch(url, headers=await self.auth_headers, json=data) as resp:
            if resp.status != 200:
                print(await resp.text())
                raise Auth0Error(f'Error {resp.status}')
            self._cache.pop(('api_permissions',), None)
            return True


class Auth0Error(Exception):
    pass
