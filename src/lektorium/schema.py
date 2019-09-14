import abc
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

    def resolve_production_url(parent, info):
        return parent.site.production_url

    def resolve_staging_url(parent, info):
        return parent.site.staging_url

    def resolve_site_name(parent, info):
        return parent.site.site_name

    def resolve_parked(parent, info):
        return not bool(parent.get('edit_url', None))

    def get(self, key, default):
        # FIXME: remove this hack
        if key == 'edit_url':
            return self.edit_url
        raise KeyError(key)


class MutationResult(ObjectType):
    ok = Boolean()


class MutationBase(Mutation):
    Output = MutationResult

    @abc.abstractmethod
    def mutate(root, info, session_id):
        pass


class DestroySession(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        try:
            info.context['repo'].destroy_session(session_id)
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class ParkSession(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        try:
            info.context['repo'].park_session(session_id)
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class Stage(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        try:
            info.context['repo'].stage(session_id)
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class RequestRelease(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        try:
            info.context['repo'].request_release(session_id)
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class UnparkSession(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        try:
            info.context['repo'].unpark_session(session_id)
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class CreateSession(MutationBase):
    class Arguments:
        site_id = String()

    @classmethod
    def mutate(cls, root, info, site_id):
        try:
            info.context['repo'].create_session(site_id)
        except lektorium.repo.ExceptionBase:
            return MutationResult(ok=False)
        return MutationResult(ok=True)


class MutationQuery(ObjectType):
    destroy_session = DestroySession.Field()
    create_session = CreateSession.Field()
    park_session = ParkSession.Field()
    unpark_session = UnparkSession.Field()
    stage = Stage.Field()
    request_release = RequestRelease.Field()


class Query(ObjectType):
    sites = List(Site)
    sessions = List(Session, parked=Boolean(default_value=False))

    @staticmethod
    def sessions_list(repo):
        for site in repo.sites:
            site = Site(**site)
            for session in site.sessions or ():
                yield dict(**session, site=site)

    def resolve_sites(root, info):
        repo = info.context['repo']
        return [Site(**x) for x in repo.sites]

    def resolve_sessions(root, info, parked):
        repo = info.context['repo']
        sessions = (Session(**x) for x in Query.sessions_list(repo))
        return [x for x in sessions if bool(x.edit_url) != parked]
