import asyncio
import time

import wrapt
from aiohttp import ClientSession
from cached_property import cached_property


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
        super().__init__(*args, **kwargs)

    @cached_property
    def lock(self):
        return asyncio.Lock()

    async def _request(self, *args, **kwargs):
        async with self.lock:
            sleep_time = self.last_request_time + self.DELAY - time.time()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self.last_request_time = time.time()
            return await super()._request(*args, **kwargs)


class Auth0Client:
    CACHE_VALID_PERIOD = 60
    CACHE_USERS_ALIAS = 'users'
    CACHE_USER_PERMISSIONS_ALIAS = 'user_permissions'
    CACHE_API_PERMISSIONS_ALIAS = 'api_permissions'

    def __init__(self, auth):
        self._cache = dict()
        self.base_url = f'https://{auth["data-auth0-domain"]}'
        self.token_url = f'{self.base_url}/oauth/token'
        self.api_id = auth['data-auth0-api']
        self.audience = f'{self.base_url}/api/v2'
        self.data = {
            'client_id': auth['data-auth0-management-id'],
            'client_secret': auth['data-auth0-management-secret'],
            'audience': f'{self.audience}/',
            'grant_type': 'client_credentials',
        }
        self.token = None
        self.token_time = time.time() + self.CACHE_VALID_PERIOD

    @cached_property
    def session(self):
        return ThrottledClientSession()

    @property
    async def auth_token(self):
        if self.token is not None:
            if time.time() - self.token_time < self.CACHE_VALID_PERIOD:
                return self.token
        async with self.session.post(self.token_url, json=self.data) as resp:
            if resp.status != 200:
                self.token = None
                raise Auth0Error(f'Error {resp.status}')
            result = await resp.json()
            self.token = result['access_token']
        self.token_time = time.time()
        return self.token

    @property
    async def auth_headers(self):
        headers = {'Authorization': 'Bearer {0}'.format(await self.auth_token)}
        return headers

    @cacher(CACHE_USERS_ALIAS)
    async def get_users(self):
        params = {'fields': 'name,nickname,email,user_id', 'per_page': 100}
        url = f'{self.audience}/users'
        async with self.session.get(url, params=params, headers=await self.auth_headers) as resp:
            if resp.status != 200:
                raise Auth0Error(f'Error {resp.status}')
            users = await resp.json()
            for user in users:
                if user.get('user_id'):
                    permissions = await self.get_user_permissions(user['user_id'])
                    user['permissions'] = [permission['permission_name'] for permission in permissions]
            return users

    @cacher(CACHE_USER_PERMISSIONS_ALIAS)
    async def get_user_permissions(self, user_id):
        params = {'per_page': 100}
        url = f'{self.audience}/users/{user_id}/permissions'
        async with self.session.get(url, params=params, headers=await self.auth_headers) as resp:
            if resp.status != 200:
                raise Auth0Error(f'Error {resp.status}')
            return await resp.json()

    async def set_user_permissions(self, user_id, permissions):
        available_permissions = [x['value'] for x in await self.get_api_permissions()]
        for permission in set(permissions).difference(available_permissions):
            await self.add_api_permission(permission, permission)
        data = {'permissions': []}
        for permission in permissions:
            data['permissions'].append({
                'resource_server_identifier': self.api_id,
                'permission_name': permission
            })
        url = f'{self.audience}/users/{user_id}/permissions'
        async with self.session.post(url, json=data, headers=await self.auth_headers) as resp:
            if resp.status != 201:
                raise Auth0Error(f'Error {resp.status}')
            self._cache.pop((self.CACHE_USER_PERMISSIONS_ALIAS, user_id), None)
            self._cache.pop((self.CACHE_USERS_ALIAS,), None)
            return True

    async def delete_user_permissions(self, user_id, permissions):
        self._cache.clear()
        data = {'permissions': []}
        for permission in permissions:
            data['permissions'].append({
                'resource_server_identifier': self.api_id,
                'permission_name': permission
            })
        url = f'{self.audience}/users/{user_id}/permissions'
        async with self.session.delete(url, json=data, headers=await self.auth_headers) as resp:
            if resp.status != 204:
                raise Auth0Error(f'Error {resp.status}')
            self._cache.pop((self.CACHE_USER_PERMISSIONS_ALIAS, user_id), None)
            self._cache.pop((self.CACHE_USERS_ALIAS,), None)
            return True

    @cacher(CACHE_API_PERMISSIONS_ALIAS)
    async def get_api_permissions(self):
        params = {'per_page': 100}
        url = f'{self.audience}/resource-servers'
        async with self.session.get(url, params=params, headers=await self.auth_headers) as resp:
            if resp.status != 200:
                raise Auth0Error(f'Error {resp.status}')
            data = await resp.json()
            data = [x for x in data if x.get('identifier') == self.api_id]
            if not data:
                raise Auth0Error(f"'{self.api_id}' api was not found")
            result = data[0]['scopes']
            return result

    async def add_api_permission(self, permission_name, description):
        data = {
            'scopes': [
                {'value': permission_name, 'description': description},
                *(await self.get_api_permissions())
            ]
        }
        url = f'{self.audience}/resource-servers/{self.api_id}'
        async with self.session.patch(url, headers=await self.auth_headers, json=data) as resp:
            if resp.status != 200:
                raise Auth0Error(f'Error {resp.status}')
            self._cache.pop((self.CACHE_API_PERMISSIONS_ALIAS,), None)
            return True


class Auth0Error(Exception):
    pass
