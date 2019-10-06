import abc
import collections
import functools
import inifile
import pathlib
import shutil
import subprocess
import tempfile
import yaml

from .objects import Site
from ...utils import closer


class Storage:
    @property
    @abc.abstractmethod
    def config(self):
        """Returns Lektorium managed sites configuration.

        Configuration is dict-like object site_id->(site object) able to set
        additional items to it and control configuration saving automatically.
        Each value of dict is also dict-like object containing site properties.
        """

    @abc.abstractmethod
    def create_session(self, site_id, session_id, session_dir):
        """Creates new session.

        This method mades all mandatory actions to create new session in
        storage itself and fill session_dir with files to start lektor server
        to work on site content.
        """

    @abc.abstractmethod
    def create_site(self, lektor, name, owner, site_id):
        """Creates new site.

        Creates new site in storage and initialize it with lektor quickstart
        via provided lektor object.
        """

    @abc.abstractmethod
    def site_config(self, site_id):
        """Returns site configuration from lektorproject file.

        Returns safe (returning None's for non-existent options) dict-like
        object from site's lektorproject file for provided site_id.
        """

    @classmethod
    def init(cls, path):
        """Init new repo on specified path and return path for constructor."""
        return path


class FileConfig(dict):
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
    CONFIG_CLASS = FileConfig
    CONFIG_FILENAME = 'config.yml'

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
                        props.setdefault('name', site_id)
                        yield props
                sites = (Site(**props) for props in iter_sites(config_file))
                config = {s['site_id']: s for s in sites}
        return self.CONFIG_CLASS(self.__config_path, config)

    def create_session(self, site_id, session_id, session_dir):
        site_root = self._site_dir(site_id)
        shutil.copytree(site_root, session_dir)

    def create_site(self, lektor, name, owner, site_id):
        site_root = self._site_dir(site_id)
        lektor.quickstart(name, owner, site_root)
        return site_root, {}

    def site_config(self, site_id):
        site_root = self._site_dir(site_id)
        config = list(site_root.glob('*.lektorproject'))
        if config:
            return inifile.IniFile(config[0])
        return collections.defaultdict(type(None))

    def _site_dir(self, site_id):
        return self.root / site_id / 'master'

    @property
    def __config_path(self):
        return self.root / self.CONFIG_FILENAME

    def __repr__(self):
        return f'{self.__class__.__name__}("{str(self.root)}")'


class GitConfig(FileConfig):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        parent, name = self.path.parent, self.path.name
        subprocess.check_call(f'git add {name}', shell=True, cwd=parent)
        subprocess.check_call('git commit -m autosave', shell=True, cwd=parent)
        subprocess.check_call('git push origin', shell=True, cwd=parent)


class GitStorage(FileStorage):
    CONFIG_CLASS = GitConfig

    def __init__(self, git):
        self.git = git
        self.workdir = pathlib.Path(closer(tempfile.TemporaryDirectory()))
        lektorium_workdir = self.workdir / 'lektorium'
        lektorium_workdir.mkdir()
        subprocess.check_call(
            f'git clone {self.git} .',
            shell=True,
            cwd=lektorium_workdir
        )
        super().__init__(lektorium_workdir)

    @classmethod
    def init(cls, path):
        lektorium = (path / 'lektorium')
        lektorium.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(f'git init --bare .', shell=True, cwd=lektorium)
        return lektorium

    @property
    def config(self):
        return super().config

    def create_session(self, site_id, session_id, session_dir):
        return super().create_session(site_id, session_id, session_dir)

    def create_site(self, lektor, name, owner, site_id):
        site_workdir = self.workdir / site_id
        if site_workdir.exists():
            raise ValueError('workdir for such site-id already exists')

        site_repo = self.create_site_repo(site_id)
        lektor.quickstart(name, owner, site_workdir)
        run = functools.partial(
            subprocess.check_call,
            shell=True,
            cwd=site_workdir
        )
        run('git init')
        run(f'git remote add origin {site_repo}')
        run('git fetch')
        run('git reset origin/master')
        run('git add .')
        run('git commit -m quickstart')
        run('git push --set-upstream origin master')

        return site_workdir, dict(repo=str(site_repo))

    def create_site_repo(self, site_id):
        site_repo = self.git.parent / site_id
        if site_repo.exists():
            raise ValueError('repo for such site-id already exists')

        site_repo.mkdir()
        run = functools.partial(subprocess.check_call, shell=True)
        run('git init --bare .', cwd=site_repo)
        with tempfile.TemporaryDirectory() as workdir:
            run = functools.partial(run, cwd=workdir)
            run(f'git clone {site_repo} .')
            run('git commit -m initial --allow-empty')
            run('git push')

        return site_repo

    def site_config(self, site_id):
        return collections.defaultdict(type(None))

    def _site_dir(self, site_id):
        if site_id in self.config:
            site_dir = self.workdir / site_id
            if not site_dir.exists():
                site_repo = self.config[site_id].get('repo', None)
                branch = self.config[site_id].get('branch', '')
                if branch:
                    branch = f'-b {branch}'
                subprocess.check_call(
                    f'git clone {site_repo} {branch} {site_dir}',
                    shell=True
                )
            return site_dir
        raise RuntimeError('wrong site request')

    def __repr__(self):
        name = self.__class__.__name__
        return f'{name}("{str(self.git)}"@"{str(self.root)}")'
