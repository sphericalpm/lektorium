import datetime
from typing import (
    Generator,
    Iterable,
    Mapping,
    Optional,
    Tuple,
)

import dateutil.parser
from .interface import (
    DuplicateEditSession,
    Repo as BaseRepo,
    SessionNotFound,
    InvalidSessionState,
)


class Session(dict):
    @property
    def edit_url(self) -> Optional[str]:
        return self.get('edit_url', None)


SITES = [{
    'site_id': 'bow',
    'site_name': 'Buy Our Widgets',
    'production_url': 'https://bow.acme.com',
    'staging_url': 'https://bow-test.acme.com',
    'custodian': 'Max Jekov',
    'custodian_email': 'mj@acme.com',
    'sessions': [Session(x) for x in [{
        'session_id': 'widgets-1',
        'edit_url': 'https://cmsdciks.cms.acme.com',
        'view_url': 'https://cmsdciks.build.acme.com',
        'creation_time': dateutil.parser.parse('2019-07-19 10:18 UTC'),
        'custodian': 'Max Jekov',
        'custodian_email': 'mj@acme.com',
    }]],
}, {
    'site_id': 'uci',
    'site_name': 'Underpants Collectors International',
    'production_url': 'https://uci.com',
    'staging_url': 'https://uci-staging.acme.com',
    'custodian': 'Mikhail Vartanyan',
    'custodian_email': 'mv@acme.com',
    'sessions': [Session(x) for x in [{
        'session_id': 'pantssss',
        'view_url': 'https://smthng.uci.com',
        'creation_time': dateutil.parser.parse('2019-07-18 11:33 UTC'),
        'custodian': 'Brian',
        'custodian_email': 'brian@splitter.il',
        'parked_time': dateutil.parser.parse('2019-07-18 11:53 UTC'),
    }, {
        'session_id': 'pantss1',
        'view_url': 'https://smthng-mu.uci.com',
        'creation_time': dateutil.parser.parse('2019-07-18 11:34 UTC'),
        'custodian': 'Muen',
        'custodian_email': 'muen@flicker.tr',
        'parked_time': dateutil.parser.parse('2019-07-18 11:54 UTC'),
    }]],
}, {
    'site_id': 'ldi',
    'site_name': 'Liver Donors Inc.',
    'production_url': 'https://liver.do',
    'staging_url': 'https://pancreas.acme.com',
    'custodian': 'Brian',
    'custodian_email': 'brian@splitter.il'
}]


class Repo(BaseRepo):
    def __init__(self, data: Mapping) -> None:
        self.data = data

    @property
    def sites(self) -> Iterable:
        yield from self.data

    @property
    def sessions(self) -> Mapping:
        return {
            session['session_id']: (session, site)
            for site in self.data
            for session in site.get('sessions', ())
        }

    @property
    def parked_sessions(self) -> Generator:
        yield from filter(
            lambda s: not bool(s[0].get('edit_url', None)),
            self.sessions.values()
        )

    def create_session(
        self,
        site_id: str,
        custodian: Optional[Tuple[str, str]] = None,
    ) -> str:
        custodian_name, custodian_email = custodian or self.DEFAULT_USER
        site = {x['site_id']: x for x in self.sites}[site_id]
        if any(s.get('edit_url', None) for s in site.get('sessions', ())):
            raise DuplicateEditSession()
        session_id = self.generate_session_id()
        site.setdefault('sessions', []).append(dict(
            session_id=session_id,
            view_url=f'https://{session_id}-created.example.com',
            edit_url=f'https://edit.{session_id}-created.example.com',
            creation_time=datetime.datetime.now(),
            custodian=custodian_name,
            custodian_email=custodian_email,
        ))
        return session_id

    def destroy_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            raise SessionNotFound()
        site = self.sessions[session_id][1]
        site['sessions'] = [
            x for x in site['sessions']
            if x['session_id'] != session_id
        ]

    def park_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            raise SessionNotFound()
        session = self.sessions[session_id][0]
        if session.pop('edit_url', None) is None:
            raise InvalidSessionState()
        session['parked_time'] = datetime.datetime.now()

    def unpark_session(self, session_id: str) -> None:
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        if session.get('edit_url', None) is not None:
            raise InvalidSessionState()
        if any(s.get('edit_url', None) for s in site.get('sessions', ())):
            raise DuplicateEditSession()
        edit_url = f'https://{session_id}-unparked.example.com'
        session['edit_url'] = edit_url
        session.pop('parked_time', None)
