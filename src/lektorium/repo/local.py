import abc
import atexit
import collections.abc
import contextlib
import datetime
import os
import pathlib
import random
import shutil
import subprocess
import tempfile

import bidict
import yaml
from cached_property import cached_property

from .interface import (
    Repo as BaseRepo,
    DuplicateEditSession,
    InvalidSessionState,
    SessionNotFound,
)


class Site(collections.abc.Mapping):
    ATTR_MAPPING = bidict.bidict({
        'name': 'site_name',
        'email': 'custodian_email',
        'owner': 'custodian',
    })

    def __init__(self, site_id, production_url, **props):
        self.data = dict(props)
        restricted_keys = ('sessions', 'production_url', 'staging_url')
        if set(self.data.keys()).intersection(restricted_keys):
            raise RuntimeError()
        self.data['site_id'] = site_id
        self.data['staging_url'] = None
        self.production_url = production_url
        self.sessions = {}

    def __getitem__(self, key):
        if key == 'sessions':
            return list(self.sessions.values())
        return self.data[key]

    def __iter__(self):
        for k in self.data:
            yield self.ATTR_MAPPING.get(k, k)
        yield 'sessions'
        yield 'production_url'

    def __len__(self):
        return len(self.data) + 2


class Session(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def parked(self):
        return not bool(self['edit_url'])


class Config(dict):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        with self.path.open('wb') as config_file:
            config = {
                k: {
                    sk: sv
                    for sk, sv in v.data.items()
                    if sk not in ('site_id', 'staging_url')
                } for k, v in self.items()
            }
            config_file.write(yaml.dump(config).encode())


class Server(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def serve_lektor(self, path):
        pass

    @abc.abstractmethod
    def serve_static(self, path):
        pass

    @abc.abstractmethod
    def stop_server(self, path):
        pass


class Lektor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_site(cls, name, owner, folder):
        raise NotImplementedError()


class LocalLektor(Lektor):
    @classmethod
    def create_site(cls, name, owner, folder):
        proc = subprocess.Popen(
            'lektor quickstart',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        proc.communicate(input=os.linesep.join((
            name,
            owner,
            str(folder),
            'Y',
            'Y',
            '',
        )).encode())
        if proc.wait() != 0:
            raise RuntimeError()


class FakeLektor(Lektor):
    @classmethod
    def create_site(cls, name, owner, folder):
        folder.mkdir(parents=True)


class FakeServer(Server):
    def __init__(self):
        self.serves = {}

    def generate_port(self):
        port = None
        while not port or port in self.serves.values():
            port = random.randint(5000, 6000)
        return port

    def serve_lektor(self, path):
        if path in self.serves:
            raise RuntimeError()
        port = self.generate_port()
        self.serves[path] = port
        return self.server_url(path)

    def stop_server(self, path):
        self.serves.pop(path)

    def server_url(self, path):
        return f'http://localhost:{self.serves[path]}'

    serve_static = serve_lektor


class Repo(BaseRepo):
    def __init__(self, root_dir, server, lektor=LocalLektor):
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
                config = {
                    site_id: Site(
                        site_id,
                        production_url=self.server.serve_static(
                            self.root_dir / site_id / 'master',
                        ),
                        **props
                    ) for site_id, props in yaml.load(config_file).items()
                }
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
        self.server.stop_server(session_dir)
        shutil.rmtree(session_dir)
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
            production_url=self.server.serve_lektor(master_path)
        ))
