import collections.abc
import os
import pathlib
import subprocess

import bidict
import yaml
from cached_property import cached_property

from .interface import Repo as BaseRepo


class Site(collections.abc.Mapping):
    ATTR_MAPPING = bidict.bidict({
        'name': 'site_name',
        'staging': 'staging_url',
        'production': 'production_url',
        'email': 'custodian_email',
        'owner': 'custodian',
    })

    def __init__(self, site_id, **props):
        self.data = dict(props)
        self.data['site_id'] = site_id
        if self.data.get('sessions') is not None:
            raise RuntimeError()

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        for k in self.data:
            yield self.ATTR_MAPPING.get(k, k)
        yield 'sessions'

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
                    if sk != 'site_id'
                } for k, v in self.items()
            }
            config_file.write(yaml.dump(config).encode())


class Repo(BaseRepo):
    def __init__(self, root_dir):
        self.root_dir = pathlib.Path(root_dir)

    @cached_property
    def config(self):
        config_path = (self.root_dir / 'config.yml')
        config = {}
        if config_path.exists():
            with config_path.open('rb') as config_file:
                config = {
                    site_id: Site(site_id, **props)
                    for site_id, props in yaml.load(config_file).items()
                }
        return Config(config_path, config)

    @property
    def sites(self):
        yield from self.config.values()

    @property
    def sessions(self):
        raise NotImplementedError()

    @property
    def parked_sessions(self):
        raise NotImplementedError()

    def create_session(self, site_id, custodian=None):
        raise NotImplementedError()

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
        proc.communicate(input=os.linesep.join((
            name,
            owner,
            str(self.root_dir / site_id / 'master'),
            'Y',
            'Y',
            '',
        )).encode())
        if proc.wait() != 0:
            raise RuntimeError()
        self.config[site_id] = Site(site_id, **dict(
            name=name,
            owner=owner,
            email=email
        ))
