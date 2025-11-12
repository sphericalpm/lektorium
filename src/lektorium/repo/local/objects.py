import collections

import bidict


class Site(collections.abc.Mapping):
    ATTR_MAPPING = bidict.bidict(
        {
            'name': 'site_name',
            'email': 'custodian_email',
            'owner': 'custodian',
        }
    )
    RESTRICTED_KEYS = ('sessions', 'staging_url')

    def __init__(self, site_id, production_url, **props):
        self.data = dict(props)
        if set(self.data.keys()).intersection(self.RESTRICTED_KEYS):
            raise ValueError('Site constructor called with restricted param')
        self.data['site_id'] = site_id
        self.data['staging_url'] = None
        self.production_url = production_url
        self.sessions = {}

    def __getitem__(self, key):
        if key == 'sessions':
            return list(self.sessions.values())
        elif key == 'production_url':
            result = self.production_url
            if callable(result):
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
        if key == 'edit_url':
            if callable(result):
                self['edit_url'], result = result()
            if isinstance(result, (list, tuple)):
                self['edit_url'], self['preview_url'], self['legacy_admin_url'] = result
                result, _ = result
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

    @property
    def preview_url(self):
        return self['preview_url']

    @property
    def legacy_admin_url(self):
        return self['legacy_admin_url']
