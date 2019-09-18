import atexit
import collections.abc
import contextlib
import datetime
import functools
import inifile
import pathlib
import shutil
import tempfile

import bidict
import yaml
from cached_property import cached_property

from ..interface import (
    Repo as BaseRepo,
    DuplicateEditSession,
    InvalidSessionState,
    SessionNotFound,
)
from .config import Config


class Site(collections.abc.Mapping):
    ATTR_MAPPING = bidict.bidict({
        'name': 'site_name',
        'email': 'custodian_email',
        'owner': 'custodian',
    })

    def __init__(self, site_id, production_url, **props):
        self.data = dict(props)
        restricted_keys = ('sessions', 'staging_url')
        if set(self.data.keys()).intersection(restricted_keys):
            raise RuntimeError()
        self.data['site_id'] = site_id
        self.data['staging_url'] = None
        self.production_url = production_url
        self.sessions = {}

    def __getitem__(self, key):
        if key == 'sessions':
            return list(self.sessions.values())
        elif key == 'production_url':
            result = self.production_url
            if callable(self.production_url):
                self.production_url, result = result()
            return result
        elif key in self.ATTR_MAPPING.inverse:
            return self[self.ATTR_MAPPING.inverse[key]]
        return self.data[key]

    def __iter__(self):
        for k in self.data:
            yield self.ATTR_MAPPING.get(k, k)
        yield 'sessions'
        yield 'production_url'

    def __len__(self):
        return len(self.data) + 2


class Session(collections.abc.Mapping):
    def __init__(self, *args, **kwargs):
        self.data = dict(*args, **kwargs)

    def __getitem__(self, key):
        result = self.data[key]
        if key == 'edit_url' and callable(result):
            self[key], result = result()
        return result

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        yield from self.data

    def __len__(self):
        return len(self.data)

    def pop(self, key, default):
        return self.data.pop(key, default)

    @property
    def parked(self):
        return not bool(self['edit_url'])

    @property
    def edit_url(self):
        return self['edit_url']


class Repo(BaseRepo):
    def __init__(self, root_dir, server, lektor):
        self.root_dir = pathlib.Path(root_dir)
        self.server = server
        self.lektor = lektor

    @cached_property
    def session_dir(self):
        result = tempfile.TemporaryDirectory()
        closer = contextlib.ExitStack()
        result = closer.enter_context(result)
        atexit.register(closer.close)
        return pathlib.Path(result)

    @cached_property
    def config(self):
        config_path = (self.root_dir / 'config.yml')
        config = {}
        if config_path.exists():
            with config_path.open('rb') as config_file:
                def iter_sites(config_file):
                    for site_id, props in yaml.load(config_file).items():
                        url = props.pop('url', None)
                        if url is None:
                            site_root = self.root_dir / site_id / 'master'
                            config = list(site_root.glob('*.lektorproject'))
                            if config:
                                config = inifile.IniFile(config[0])
                                name = config.get('project.name')
                                if name is not None:
                                    props['name'] = name
                                project_url = config.get('project.url')
                                if project_url is not None:
                                    url = project_url
                            if url is None:
                                url = self.server.serve_static(site_root)
                        props['production_url'] = url
                        props['site_id'] = site_id
                        yield props
                sites = (Site(**props) for props in iter_sites(config_file))
                config = {s['site_id']: s for s in sites}
        return Config(config_path, config)

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

    def create_session(self, site_id, custodian=None):
        custodian, custodian_email = custodian or self.DEFAULT_USER
        site = self.config[site_id]
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        session_id = self.generate_session_id()
        session_dir = self.session_dir / site_id / session_id
        shutil.copytree(self.root_dir / site_id / 'master', session_dir)
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
        session_dir = self.session_dir / site['site_id'] / session_id
        self.server.stop_server(
            session_dir,
            functools.partial(shutil.rmtree, session_dir)
        )
        site.sessions.pop(session_id)

    def park_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        session_dir = self.session_dir / site['site_id'] / session_id
        if session.parked:
            raise InvalidSessionState()
        self.server.stop_server(session_dir)
        session['edit_url'] = None
        session['parked_time'] = datetime.datetime.now()

    def unpark_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        session_dir = (self.session_dir / site['site_id'] / session_id)
        if not session.parked:
            raise InvalidSessionState()
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        session['edit_url'] = self.server.serve_lektor(session_dir)
        session.pop('parked_time', None)

    def create_site(self, site_id, name, owner=None):
        owner, email = owner or self.DEFAULT_USER
        master_path = self.root_dir / site_id / 'master'
        self.lektor.create_site(name, owner, master_path)
        self.config[site_id] = Site(site_id, **dict(
            name=name,
            owner=owner,
            email=email,
            production_url=self.server.serve_static(master_path)
        ))