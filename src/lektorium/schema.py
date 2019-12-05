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


class Releasing(ObjectType):
    site_id = String()
    site_name = String()
    title = String()
    id = String()
    target_branch = String()
    source_branch = String()
    state = String()
    web_url = String()


def permissions_checker(required):
    @wrapt.decorator
    async def wrapper(wrapped, instance, args, kwargs):
        if required is not None and len(required):
            info = args[0]
            permissions = set(info.context.get('user_permissions', []))
            if not required.difference(permissions):
                return await wrapped(*args, **kwargs)
        return ()
    return wrapper


class Query(ObjectType):
    sites = List(Site)
    sessions = List(Session, parked=Boolean(default_value=False))
    releasing = List(Releasing)

    @staticmethod
    def sessions_list(repo):
        for site in repo.sites:
            site = Site(**site)
            for session in site.sessions or ():
                yield dict(**session, site=site)

    @permissions_checker({'read:sites'})
    async def resolve_sites(self, info):
        repo = info.context['repo']
        return [Site(**x) for x in repo.sites]

    async def resolve_sessions(self, info, parked):
        repo = info.context['repo']
        sessions = (Session(**x) for x in Query.sessions_list(repo))
        return [x for x in sessions if bool(x.edit_url) != parked]

    async def resolve_releasing(self, info):
        repo = info.context['repo']
        return [Releasing(**x) for x in repo.releasing]


class MutationResult(ObjectType):
    ok = Boolean()


class MutationBase(Mutation):
    Output = MutationResult

    @classmethod
    def has_permission(cls, root, info, **kwargs):
        if cls.REQUIRES is None:
            return True
        permissions = set(info.context.get('user_permissions', []))
        if not cls.REQUIRES.difference(permissions):
            return True
        return False

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        if not cls.has_permission(root, info, **kwargs):
            return MutationResult(ok=False)
        try:
            method = getattr(info.context['repo'], cls.REPO_METHOD)
            result = method(**kwargs)
            if isinstance(result, Future) or iscoroutine(result):
                await result
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class DestroySession(MutationBase):
    REPO_METHOD = 'destroy_session'
    REQUIRES = None

    class Arguments:
        session_id = String()


class ParkSession(MutationBase):
    REPO_METHOD = 'park_session'
    REQUIRES = None

    class Arguments:
        session_id = String()


class RequestRelease(MutationBase):
    REPO_METHOD = 'request_release'
    REQUIRES = None

    class Arguments:
        session_id = String()


class UnparkSession(MutationBase):
    REPO_METHOD = 'unpark_session'
    REQUIRES = None

    class Arguments:
        session_id = String()


class CreateSession(MutationBase):
    REPO_METHOD = 'create_session'
    REQUIRES = None

    class Arguments:
        site_id = String()

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        jwt_user = info.context.get('userdata')
        return super().mutate(root, info, custodian=jwt_user, **kwargs)


class CreateSite(MutationBase):
    REQUIRES = {'create:site'}
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
