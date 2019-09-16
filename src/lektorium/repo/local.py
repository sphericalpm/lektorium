import abc
import atexit
import collections.abc
import contextlib
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

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        for k in self.data:
            yield self.ATTR_MAPPING.get(k, k)
        yield 'sessions'
        yield 'production_url'

    def __len__(self):
        return len(self.data)


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


class FakeServer(Server):
    def __init__(self):
        self.serves = {}

    def generate_port(self):
        port = None
        while not port and port in self.serves.values():
            port = random.randint(5000, 6000)
        return port

    def serve_lektor(self, path):
        if path in self.serves:
            raise RuntimeError()
        port = self.generate_port()
        self.serves[path] = port
        return f'http://localhost:{port}'

    def stop_server(self, path):
        self.serves.pop(path)

    serve_static = serve_lektor


class Repo(BaseRepo):
    def __init__(self, root_dir, server):
        self.root_dir = pathlib.Path(root_dir)
        self.server = server

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
            for site in self.session_dir.iterdir():
                for session in site.iterdir():
                    session_id, _, _ = session.name.partition('.')
                    yield session_id, (None, self.config[site.name])
        return dict(iterate())

    @property
    def parked_sessions(self):
        raise NotImplementedError()

    def create_session(self, site_id, custodian=None):
        custodian, custodian_email = custodian or self.DEFAULT_USER
        if (self.session_dir / site_id).exists():
            for s in (self.session_dir / site_id).iterdir():
                if not s.name.endswith('.parked'):
                    raise DuplicateEditSession()
        session_id = self.generate_session_id()
        shutil.copytree(
            self.root_dir / site_id / 'master',
            self.session_dir / site_id / session_id,
        )
        return session_id

    def destroy_session(self, session_id):
        raise NotImplementedError()

    def park_session(self, session_id):
        raise NotImplementedError()

    def unpark_session(self, session_id):
        raise NotImplementedError()

    def create_site(self, site_id, name, owner=None):
        owner, email = owner or self.DEFAULT_USER
        proc = subprocess.Popen(
            'lektor quickstart',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        master_path = self.root_dir / site_id / 'master'
        proc.communicate(input=os.linesep.join((
            name,
            owner,
            str(master_path),
            'Y',
            'Y',
            '',
        )).encode())
        if proc.wait() != 0:
            raise RuntimeError()
        self.config[site_id] = Site(site_id, **dict(
            name=name,
            owner=owner,
            email=email,
            production_url=self.server.serve_lektor(master_path)
        ))
