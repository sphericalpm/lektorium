import asyncio
import collections.abc
from datetime import datetime
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
        self.sessions_initialized = False
        self.init_sites()

    def init_sites(self):
        for site_id, site in self.config.items():
            site_dir = (self.sessions_root / site_id)
            if site_dir.exists():
                for session_dir in site_dir.iterdir():
                    session = Session(
                        session_id=session_dir.name,
                        creation_time=datetime.fromtimestamp(session_dir.lstat().st_ctime),
                        custodian=site['owner'],
                        custodian_email=site['email'],
                        parked_time=datetime.fromtimestamp(session_dir.lstat().st_mtime),
                        edit_url=None,
                    )
                    site.sessions[session['session_id']] = session

    async def init_sessions(self):
        if not self.sessions_initialized:
            sessions = self.server.sessions
            if asyncio.iscoroutine(sessions):
                sessions = await sessions
            for session in sessions:
                session = dict(session)
                site_id = session.pop('site_id', None)
                if site_id is None or site_id not in self.config:
                    continue
                session = Session(session)
                session_id = session['session_id']
                self.config[site_id].sessions[session_id] = session
            self.sessions_initialized = True

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

    @property
    def releasing(self):
        for site_id, site in self.config.items():
            for merge_request_data in self.storage.get_merge_requests(site_id):
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
            creation_time=datetime.now(),
            custodian=custodian,
            custodian_email=custodian_email,
        )
        session_object['edit_url'] = self.server.serve_lektor(
            session_dir, {
                **session_object,
                'site_id': site_id
            }
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
        session['parked_time'] = datetime.now()

    def unpark_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        if not session.parked:
            raise InvalidSessionState()
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        site_id = site['site_id']
        session['edit_url'] = self.server.serve_lektor(
            self.sessions_root / site_id / session_id,
            {**session, 'site_id': site_id},
        )
        session.pop('parked_time', None)

    async def create_site(self, site_id, name, owner=None):
        owner, email = owner or self.DEFAULT_USER
        site_root, site_options = await self.storage.create_site(
            self.lektor,
            name,
            owner,
            site_id
        )

        production_url = site_options.pop('production_url', None)
        if production_url is None:
            production_url = site_options.get('url', None)
        if production_url is None:
            production_url = self.server.serve_static(site_root)

        self.config[site_id] = Site(site_id, production_url, **dict(
            name=name,
            owner=owner,
            email=email,
            **site_options,
        ))

    def request_release(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        if session.parked:
            raise InvalidSessionState()
        site_id = site['site_id']
        session_dir = self.sessions_root / site_id / session_id
        self.storage.request_release(site_id, session_id, session_dir)
        self.destroy_session(session_id)

    def __repr__(self):
        qname = f'{self.__class__.__module__}.{self.__class__.__name__}'
        return f'{qname}({self.storage}, {self.server}, {self.lektor})'
