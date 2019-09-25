import abc
import collections
import inifile
import pathlib
import shutil
import yaml
from .objects import Site


class Storage:
    @property
    @abc.abstractmethod
    def config(self):
        """Returns Lektorium managed sites configuration.

        Configuration is dict-like object site_id->(site object) able to set
        additional items to it and control configuration saving automatically.
        Each value of dict is also dict-like object containing site properties.
        """
        pass

    @abc.abstractmethod
    def create_session(self, site_id, session_id, session_dir):
        """Creates new session.

        This method mades all mandatory actions to create new session in
        storage itself and fill session_dir with files to start lektor server
        to work on site content.
        """
        pass

    @abc.abstractmethod
    def create_site(self, lektor, name, owner, site_id):
        """Creates new site.

        Creates new site in repository and initialize it with lektor quickstart.
        """
        pass

    @abc.abstractmethod
    def site_config(self, site_id):
        """Returns site configuration from lektorproject file.

        Returns safe dict-like object (returning None's) for non-existent
        options from site's lektorproject file.
        """
        pass


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


class FileStorage(Storage):
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()

    @property
    def config(self):
        config = {}
        if self.__config_path.exists():
            with self.__config_path.open('rb') as config_file:
                def iter_sites(config_file):
                    config_data = yaml.load(config_file, Loader=yaml.Loader)
                    for site_id, props in config_data.items():
                        url = props.pop('url', None)
                        config = self.site_config(site_id)
                        name = config.get('project.name')
                        if name is not None:
                            props['name'] = name
                        if url is None:
                            url = config.get('project.url')
                        props['production_url'] = url
                        props['site_id'] = site_id
                        yield props
                sites = (Site(**props) for props in iter_sites(config_file))
                config = {s['site_id']: s for s in sites}
        return Config(self.__config_path, config)

    def create_session(self, site_id, session_id, session_dir):
        site_root = self.__site_dir(site_id)
        shutil.copytree(site_root, session_dir)

    def create_site(self, lektor, name, owner, site_id):
        site_root = self.__site_dir(site_id)
        lektor.create_site(name, owner, site_root)
        return site_root

    def site_config(self, site_id):
        site_root = self.__site_dir(site_id)
        config = list(site_root.glob('*.lektorproject'))
        if config:
            return inifile.IniFile(config[0])
        return collections.defaultdict(type(None))

    def __site_dir(self, site_id):
        return self.root / site_id / 'master'

    @property
    def __config_path(self):
        return self.root / 'config.yml'
