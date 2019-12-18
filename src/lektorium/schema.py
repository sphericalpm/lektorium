from os import environ
from asyncio import Future, iscoroutine

import wrapt
from graphene import (
    Boolean,
    DateTime,
    Field,
    List,
    Mutation,
    ObjectType,
    String,
)

from .jwt import GraphExecutionError
import lektorium.repo
from lektorium.auth0 import Auth0Error


class Site(ObjectType):
    def __init__(self, **kwargs):
        super().__init__(**{
            k: v for k, v in kwargs.items()
            if k in self._meta.fields
        })

    site_id = String()
    site_name = String()
    custodian = String()
    custodian_email = String()
    production_url = String()
    staging_url = String()
    sessions = List(lambda: Session)


class Session(ObjectType):
    session_id = String()
    site_name = String()
    edit_url = String()
    view_url = String()
    creation_time = DateTime()
    custodian = String()
    custodian_email = String()
    parked_time = DateTime()
    production_url = String()
    staging_url = String()
    site = Field(Site)
    parked = Boolean()

    def resolve_production_url(self, info):
        return self.site.production_url

    def resolve_staging_url(self, info):
        return self.site.staging_url

    def resolve_site_name(self, info):
        return self.site.site_name

    def resolve_parked(self, info):
        return not bool(self.edit_url)


class User(ObjectType):
    user_id = String()
    email = String()
    name = String()
    nickname = String()
    permissions = List(String)


class Permission(ObjectType):
    permission_name = String()
    description = String()
    resource_server_name = String()
    resource_server_identifier = String()
    sources = String()


class ApiPermission(ObjectType):
    value = String()
    description = String()


class Releasing(ObjectType):
    site_id = String()
    site_name = String()
    title = String()
    id = String()
    target_branch = String()
    source_branch = String()
    state = String()
    web_url = String()


def skip_permissions_check():
    return environ.get('CHECKPERMISSIONS', '') == 'disable'


def get_user_permissions(info):
    permissions = set(info.context.get('user_permissions', []))
    if not permissions:
        raise GraphExecutionError(
            'User has no permissions',
            code=403
        )
    return permissions


def require_permissions(required):
    @wrapt.decorator
    async def wrapper(wrapped, instance, args, kwargs):
        if skip_permissions_check():
            return await wrapped(*args, **kwargs)
        permissions = get_user_permissions(args[0])
        if required is not None and len(required):
            if not required.difference(permissions):
                return await wrapped(*args, **kwargs)
        return ()
    return wrapper


class Query(ObjectType):
    sites = List(Site)
    sessions = List(Session, parked=Boolean(default_value=False))
    users = List(User)
    permissions = List(Permission, user_id=String())
    available_permissions = List(ApiPermission)
    releasing = List(Releasing)

    @staticmethod
    def sessions_list(repo):
        for site in repo.sites:
            site = Site(**site)
            for session in site.sessions or ():
                yield dict(**session, site=site)

    @require_permissions({'read:sites'})
    async def resolve_sites(self, info):
        repo = info.context['repo']
        return [Site(**x) for x in repo.sites]

    @require_permissions({'read:sessions'})
    async def resolve_sessions(self, info, parked):
        repo = info.context['repo']
        sessions = (Session(**x) for x in Query.sessions_list(repo))
        return [x for x in sessions if bool(x.edit_url) != parked]

    @require_permissions({'read:users'})
    async def resolve_users(self, info):
        auth0_client = info.context['auth0_client']
        return [User(**x) for x in await auth0_client.get_users()]

    @require_permissions({'read:user-permissions'})
    async def resolve_permissions(self, info, user_id):
        auth0_client = info.context['auth0_client']
        return [Permission(**x) for x in await auth0_client.get_user_permissions(user_id)]

    @require_permissions({'read:all-permissions'})
    async def resolve_available_permissions(self, info):
        auth0_client = info.context['auth0_client']
        return [ApiPermission(**x) for x in await auth0_client.get_api_permissions()]

    @require_permissions({'read:releases'})
    async def resolve_releasing(self, info):
        repo = info.context['repo']
        return [Releasing(**x) for x in repo.releasing]


class MutationResult(ObjectType):
    ok = Boolean()
    nopermission = Boolean(default_value=False)


class MutationBase(Mutation):
    Output = MutationResult

    @classmethod
    def has_permission(cls, root, info, **kwargs):
        if skip_permissions_check():
            return True
        permissions = get_user_permissions(info)
        if cls.REQUIRES is None:
            return True
        if not cls.REQUIRES.difference(permissions):
            return True
        return False

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        if not cls.has_permission(root, info, **kwargs):
            return MutationResult(ok=False, nopermission=True)
        try:
            method = getattr(info.context['repo'], cls.REPO_METHOD)
            result = method(**kwargs)
            if isinstance(result, Future) or iscoroutine(result):
                await result
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class AddPermissions(MutationBase):
    REQUIRES = {'add:permission'}
    REPO_METHOD = 'set_user_permissions'

    class Arguments:
        user_id = String()
        permissions = List(String)

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        if not cls.has_permission(root, info, **kwargs):
            return MutationResult(ok=False, nopermission=True)
        try:
            method = getattr(info.context['auth0_client'], cls.REPO_METHOD)
            result = method(**kwargs)
            if isinstance(result, Future) or iscoroutine(result):
                await result
        except Auth0Error:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class DeletePermissions(MutationBase):
    REQUIRES = {'delete:permission'}
    REPO_METHOD = 'delete_user_permissions'

    class Arguments:
        user_id = String()
        permissions = List(String)

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        if not cls.has_permission(root, info, **kwargs):
            return MutationResult(ok=False, nopermission=True)
        try:
            method = getattr(info.context['auth0_client'], cls.REPO_METHOD)
            result = method(**kwargs)
            if isinstance(result, Future) or iscoroutine(result):
                await result
        except Auth0Error:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class DestroySession(MutationBase):
    REQUIRES = {'delete:session'}
    REPO_METHOD = 'destroy_session'

    class Arguments:
        session_id = String()


class ParkSession(MutationBase):
    REQUIRES = {'edit:session'}
    REPO_METHOD = 'park_session'

    class Arguments:
        session_id = String()


class RequestRelease(MutationBase):
    REQUIRES = {'add:release'}
    REPO_METHOD = 'request_release'

    class Arguments:
        session_id = String()


class UnparkSession(MutationBase):
    REQUIRES = {'edit:session'}
    REPO_METHOD = 'unpark_session'

    class Arguments:
        session_id = String()


class CreateSession(MutationBase):
    REQUIRES = {'add:session'}
    REPO_METHOD = 'create_session'

    class Arguments:
        site_id = String()

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        jwt_user = info.context.get('userdata')
        return super().mutate(root, info, custodian=jwt_user, **kwargs)


class CreateSite(MutationBase):
    REQUIRES = {'add:site'}
    REPO_METHOD = 'create_site'

    class Arguments:
        site_id = String()
        name = String(name='siteName')

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        jwt_user = info.context.get('userdata')
        return super().mutate(root, info, owner=jwt_user, **kwargs)


MutationQuery = type(
    'MutationQuery', (
        ObjectType,
    ), {
        cls.REPO_METHOD: getattr(cls, 'Field')()
        for cls in MutationBase.__subclasses__()
    },
)
