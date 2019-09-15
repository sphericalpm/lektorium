import collections.abc

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


class Repo(BaseRepo):
    def __init__(self, repo_root_dir):
        self.repo_root_dir = repo_root_dir

    @cached_property
    def config(self):
        with (self.repo_root_dir / 'config.yml').open('rb') as config_file:
            config = yaml.load(config_file)
            return {
                site_id: Site(site_id, **props)
                for site_id, props in config.items()
            }

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
