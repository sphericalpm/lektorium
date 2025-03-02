import functools
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

import lektorium.repo
from lektorium.auth0 import Auth0Error

from .jwt import GraphExecutionError


ADMIN = 'admin'


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
    creation_time = DateTime()
    custodian = String()
    custodian_email = String()
    parked_time = DateTime()
    production_url = String()
    staging_url = String()
    site = Field(Site)
    parked = Boolean()
    themes = List(String)

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


class Theme(ObjectType):
    name = String()
    active = Boolean()


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
    created_at = DateTime()


def skip_permissions_check(info):
    return info.context.get('skip_permissions_check', False)


def repo(method):
    def wrapper(self, info, *args, **kwargs):
        repo = info.context['repo']
        return method(self, info, *args, repo=repo, **kwargs)
    return wrapper


class PermissionError(GraphExecutionError):
    def __init__(self):
        super().__init__('User has no permission', code=403)


def get_user_permissions(info):
    permissions = set(info.context.get('user_permissions', []))
    if not permissions:
        raise PermissionError()
    return permissions


def inject_permissions(wrapped=None, admin=False):
    if wrapped is None:
        return functools.partial(inject_permissions, admin=admin)

    @wrapt.decorator
    async def wrapper(wrapped, instance, args, kwargs):
        info, *_ = args
        permissions = get_user_permissions(info)
        if skip_permissions_check(info):
            permissions = (ADMIN,)
        if admin and ADMIN not in permissions:
            return ()
        return await wrapped(*args, permissions=permissions, **kwargs)

    return wrapper(wrapped)


class Query(ObjectType):
    sites = List(Site)
    sessions = List(Session, parked=Boolean(default_value=False))
    users = List(User)
    themes = List(Theme, site_id=String(default_value=None))
    user_permissions = List(Permission, user_id=String())
    available_permissions = List(ApiPermission)
    releasing = List(Releasing)

    @staticmethod
    def sessions_list(repo):
        for site in repo.sites:
            site = Site(**site)
            for session in site.sessions or ():
                themes = []
                if bool(session.edit_url):
                    session_dir = repo.sessions_root / site.site_id / session['session_id']
                    themes = repo.storage.config_dir_themes(session_dir)
                yield dict(**session, themes=themes, site=site)

    @inject_permissions
    @repo
    async def resolve_sites(self, info, repo, permissions):
        return [
            Site(**x) for x in repo.sites
            if ADMIN in permissions or f'user:{x["site_id"]}' in permissions
        ]

    @inject_permissions
    @repo
    async def resolve_sessions(self, info, parked, repo, permissions):
        await repo.init_sessions()
        sessions = (Session(**x) for x in Query.sessions_list(repo))
        return [
            x for x in sessions
            if (
                bool(x.edit_url) != parked and (
                    ADMIN in permissions or f'user:{x.site.site_id}' in permissions
                )
            )
        ]

    @inject_permissions(admin=True)
    async def resolve_users(self, info, permissions):
        auth0_client = info.context['auth0_client']
        return [User(**x) for x in await auth0_client.get_users()]

    @repo
    def resolve_themes(self, info, site_id, repo):
        if site_id:
            return repo.storage.site_themes(site_id)[::-1]
        return [
            {'name': theme, 'active': True}
            for theme in repo.storage.themes().values()
        ]

    @inject_permissions(admin=True)
    async def resolve_user_permissions(self, info, user_id, permissions):
        auth0_client = info.context['auth0_client']
        return [Permission(**x) for x in await auth0_client.get_user_permissions(user_id)]

    @inject_permissions(admin=True)
    @repo
    async def resolve_available_permissions(self, info, repo, permissions):
        return [
            ApiPermission(v, v)
            for v in (
                'admin',
                *(f'user:{x["site_id"]}' for x in repo.sites),
            )
        ]

    @inject_permissions
    @repo
    async def resolve_releasing(self, info, repo, permissions):
        repo = info.context['repo']
        return [Releasing(**x) for x in repo.releasing]


class MutationResult(ObjectType):
    ok = Boolean()


class MutationBase(Mutation):
    Output = MutationResult
    TARGET = 'repo'

    @classmethod
    def mutate_allowed(cls, permissions, **kwargs):
        return False

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        if not skip_permissions_check(info):
            permissions = get_user_permissions(info)
            if ADMIN not in permissions:
                if not cls.mutate_allowed(permissions, **kwargs):
                    raise PermissionError()

        try:
            method = getattr(info.context[cls.TARGET], cls.REPO_METHOD)
            result = method(**kwargs)
            if isinstance(result, Future) or iscoroutine(result):
                await result
        except (Auth0Error, lektorium.repo.ExceptionBase):
            return MutationResult(ok=False)

        return MutationResult(ok=True)


class ChangePermissionsMixin:
    TARGET = 'auth0_client'

    class Arguments:
        user_id = String()
        permissions = List(String)


class AddPermissions(ChangePermissionsMixin, MutationBase):
    REPO_METHOD = 'set_user_permissions'


class DeletePermissions(ChangePermissionsMixin, MutationBase):
    REPO_METHOD = 'delete_user_permissions'


class SitePermissionMixin:
    @classmethod
    def mutate_allowed(cls, permissions, site_id, **kwargs):
        return f'user:{site_id}' in permissions


class DestroySession(SitePermissionMixin, MutationBase):
    REPO_METHOD = 'destroy_session'

    class Arguments:
        session_id = String()


class ParkSession(SitePermissionMixin, MutationBase):
    REPO_METHOD = 'park_session'

    class Arguments:
        session_id = String()


class RequestRelease(SitePermissionMixin, MutationBase):
    REPO_METHOD = 'request_release'

    class Arguments:
        session_id = String()


class UnparkSession(SitePermissionMixin, MutationBase):
    REPO_METHOD = 'unpark_session'

    class Arguments:
        session_id = String()


class CreateSession(SitePermissionMixin, MutationBase):
    REPO_METHOD = 'create_session'

    class Arguments:
        site_id = String()
        themes = List(String, required=False)

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        jwt_user = info.context.get('userdata')
        return super().mutate(root, info, custodian=jwt_user, **kwargs)


class CreateSite(MutationBase):
    REPO_METHOD = 'create_site'

    class Arguments:
        site_id = String()
        name = String(name='siteName')
        owner = String()
        themes = List(String, required=False)

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        owner = kwargs.pop('owner', None)
        if not owner:
            owner = info.context.get('userdata')
        else:
            email, _, name = owner.partition(',')
            owner = (name, email)
        return super().mutate(root, info, owner=owner, **kwargs)


MutationQuery = type(
    'MutationQuery', (
        ObjectType,
    ), {
        cls.REPO_METHOD: getattr(cls, 'Field')()
        for cls in MutationBase.__subclasses__()
    },
)
