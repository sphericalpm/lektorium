import collections.abc
import datetime
import functools
import pathlib
import shutil
import tempfile

from cached_property import cached_property

from ...utils import closer
from ..interface import (
    DuplicateEditSession,
    InvalidSessionState,
    Repo as BaseRepo,
    SessionNotFound,
)
from .objects import Session, Site


class FilteredDict(collections.abc.Mapping):
    def __init__(self, keys, dct):
        self.__keys = keys
        self.__dct = dct

    def __getitem__(self, key):
        if key not in self.__keys:
            raise KeyError(key)
        return self.__dct[key]

    @property
    def __common_keys(self):
        return set(self.__keys).intersection(self.__dct)

    def __iter__(self):
        return iter(self.__common_keys)

    def __len__(self):
        return len(self.__common_keys)


class FilteredMergeRequestData(FilteredDict):
    MERGE_REQUEST_KEYS = [
        'id',
        'source_branch',
        'state',
        'target_branch',
        'title',
        'web_url',
    ]

    def __init__(self, dct):
        super().__init__(self.MERGE_REQUEST_KEYS, dct)


class Repo(BaseRepo):
    def __init__(self, storage, server, lektor, sessions_root=None):
        self.storage = storage
        self.server = server
        self.lektor = lektor
        if sessions_root is None:
            sessions_root = closer(tempfile.TemporaryDirectory())
        self.sessions_root = pathlib.Path(sessions_root)
        self.init_sites()

    def init_sites(self):
        for site_id, site in self.config.items():
            if site.production_url is None:
                session_dir = self.sessions_root / site_id / 'production'
                self.storage.create_session(site_id, 'production', session_dir)
                site.production_url = self.server.serve_static(session_dir)

    @cached_property
    def config(self):
        return self.storage.config

    @property
    def sites(self):
        yield from self.config.values()

    @property
    def sessions(self):
        def iterate():
            for site in self.config.values():
                for session_id, session in site.sessions.items():
                    yield session_id, (session, site)
        return dict(iterate())

    @property
    def parked_sessions(self):
        for site in self.config.values():
            for session in site.sessions.values():
                if session.parked:
                    yield session

    async def releasing(self):
        for site_id, site in self.config.items():
            for merge_request_data in await self.storage.get_merge_requests(site_id):
                if merge_request_data['source_branch'].startswith('session-'):
                    yield {
                        'site_name': site['name'],
                        **FilteredMergeRequestData(merge_request_data)
                    }

    def create_session(self, site_id, custodian=None):
        custodian, custodian_email = custodian or self.DEFAULT_USER
        site = self.config[site_id]
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        session_id = self.generate_session_id()
        session_dir = self.sessions_root / site_id / session_id
        self.storage.create_session(site_id, session_id, session_dir)
        session_object = Session(
            session_id=session_id,
            creation_time=datetime.datetime.now(),
            view_url=None,
            edit_url=self.server.serve_lektor(session_dir),
            custodian=custodian,
            custodian_email=custodian_email,
        )
        self.config[site_id].sessions[session_id] = session_object
        return session_id

    def destroy_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        site = self.sessions[session_id][1]
        session_dir = self.sessions_root / site['site_id'] / session_id
        self.server.stop_server(
            session_dir,
            functools.partial(shutil.rmtree, session_dir)
        )
        site.sessions.pop(session_id)

    def park_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        session_dir = self.sessions_root / site['site_id'] / session_id
        if session.parked:
            raise InvalidSessionState()
        self.server.stop_server(session_dir)
        session['edit_url'] = None
        session['parked_time'] = datetime.datetime.now()

    def unpark_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        session_dir = self.sessions_root / site['site_id'] / session_id
        if not session.parked:
            raise InvalidSessionState()
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        session['edit_url'] = self.server.serve_lektor(session_dir)
        session.pop('parked_time', None)

    async def create_site(self, site_id, name, owner=None):
        owner, email = owner or self.DEFAULT_USER
        site_root, site_options = await self.storage.create_site(
            self.lektor,
            name,
            owner,
            site_id
        )
        if 'production_url' not in site_options:
            site_options['production_url'] = self.server.serve_static(site_root)
        self.config[site_id] = Site(site_id, **dict(
            name=name,
            owner=owner,
            email=email,
            **site_options,
        ))

    async def request_release(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        if session.parked:
            raise InvalidSessionState()
        site_id = site['site_id']
        session_dir = self.sessions_root / site_id / session_id
        await self.storage.request_release(site_id, session_id, session_dir)
        self.destroy_session(session_id)

    def __repr__(self):
        qname = f'{self.__class__.__module__}.{self.__class__.__name__}'
        return f'{qname}({self.storage}, {self.server}, {self.lektor})'
