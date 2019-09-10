from graphene import ObjectType, String, Schema, List, Field, Boolean, Mutation


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
    creation_time = String()
    custodian = String()
    custodian_email = String()
    parked_time = String()
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
        return not bool(parent.edit_url)


class DestroySession(Mutation):
    class Arguments:
        session_id = String()

    ok = Boolean()

    def mutate(root, info, session_id):
        repo = info.context['repo']
        sessions = [(s, x) for s in repo.sites for x in s.get('sessions', ())]
        for site, session in sessions:
            if session['session_id'] == session_id:
                site['sessions'] = [
                    x for x in site['session']
                    if x['session_id'] != session_id
                ]
            return DestroySession(ok=True)
        return DestroySession(ok=False)


class MutationQuery(ObjectType):
    destroy_session = DestroySession.Field()


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
