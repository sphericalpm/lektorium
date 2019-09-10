import abc
import datetime
import random
import string
from graphene import (
    Boolean,
    DateTime,
    Field,
    List,
    Mutation,
    ObjectType,
    String,
)


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


class MutationResult(ObjectType):
    ok = Boolean()


class MutationBase(Mutation):
    Output = MutationResult

    @staticmethod
    def sessions(repo):
        return {
            x['session_id']: (x, s)
            for s in repo.sites for x in s.get('sessions', ())
        }


    @abc.abstractmethod
    def mutate(root, info, session_id):
        pass


class DestroySession(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        sessions = cls.sessions(info.context['repo'])
        site = sessions[session_id][1]
        site['sessions'] = [
            x for x in site['sessions']
            if x['session_id'] != session_id
        ]
        return MutationResult(ok=True)


class ParkSession(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        sessions = cls.sessions(info.context['repo'])
        session = sessions[session_id][0]
        if session.pop('edit_url', None) is None:
            return MutationResult(ok=False)
        session['parked_time'] = datetime.datetime.now()
        return MutationResult(ok=True)


class UnparkSession(MutationBase):
    class Arguments:
        session_id = String()

    @classmethod
    def mutate(cls, root, info, session_id):
        sessions = cls.sessions(info.context['repo'])
        session = sessions[session_id][0]
        if session.get('edit_url', None) is not None:
            return MutationResult(ok=False)
        edit_url = f'https://{session_id}-unparked.example.com'
        session['edit_url'] = edit_url
        session.pop('parked_time', None)
        return MutationResult(ok=True)


class CreateSession(MutationBase):
    class Arguments:
        site_id = String()

    @classmethod
    def mutate(cls, root, info, site_id):
        repo = info.context['repo']
        site = {x['site_id']: x for x in repo.sites}[site_id]
        sessions = cls.sessions(info.context['repo'])
        session_id = None
        while not session_id or session_id in sessions:
            session_id = ''.join(random.sample(string.ascii_lowercase, 8))
        site.setdefault('sessions', []).append(dict(
            session_id=session_id,
            view_url=f'https://{session_id}-created.example.com',
            edit_url=f'https://edit.{session_id}-created.example.com',
            creation_time=datetime.datetime.now(),
            custodian='user-from-jws@example.com',
            custodian_email='User Jwt',
        ))
        return MutationResult(ok=True)


class MutationQuery(ObjectType):
    destroy_session = DestroySession.Field()
    create_session = CreateSession.Field()
    park_session = ParkSession.Field()
    unpark_session = UnparkSession.Field()


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
