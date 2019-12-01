import abc
import collections
import functools
import inifile
import logging
import pathlib
import requests
import shutil
import subprocess
import tempfile
from cached_property import cached_property
from more_itertools import one
import yaml

from .objects import Site
from .templates import (
    AWS_SHARED_CREDENTIALS_FILE_TEMPLATE,
    LECTOR_S3_SERVER_TEMPLATE,
    GITLAB_CI_TEMPLATE,
)
from ...utils import closer


run = functools.partial(subprocess.check_call, shell=True)


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
            config = {k: self.unprepare(v) for k, v in self.items()}
            config_file.write(yaml.dump(config).encode())

    @staticmethod
    def unprepare(site_config):
        return {
            sk: sv
            for sk, sv in site_config.data.items()
            if sk not in ('site_id', 'staging_url') and (
                sk != 'repo' or 'gitlab' not in site_config.data
            ) and (sk != 'name' or sv != site_config['site_id'])
        }


class FileStorageMixin:
    CONFIG_FILENAME = 'config.yml'

    @classmethod
    def load_config(cls, path, site_config_fetcher):
        config = {}
        if path.exists():
            with path.open('rb') as config_file:
                def iter_sites(config_file):
                    config_data = yaml.load(config_file, Loader=yaml.Loader)
                    for site_id, props in config_data.items():
                        url = props.get('url', None)
                        config = site_config_fetcher(site_id)
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
        return cls.CONFIG_CLASS(path, config)

    @cached_property
    def config(self):
        return self.load_config(self._config_path, self.site_config)

    @property
    def _config_path(self):
        return self.root / self.CONFIG_FILENAME


class FileStorage(FileStorageMixin, Storage):
    CONFIG_CLASS = FileConfig

    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()

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

    def get_merge_requests(self, site_id):
        logging.warn('get_merge_requests: site has no gitlab option')
        return []

    def _site_dir(self, site_id):
        return self.root / site_id / 'master'

    def __repr__(self):
        return f'{self.__class__.__name__}("{str(self.root)}")'


class GitConfig(FileConfig):
    def __getitem__(self, key):
        return self.prepare(super().__getitem__(key))

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        parent, name = self.path.parent, self.path.name
        run(f'git add {name}', cwd=parent)
        run('git commit -m autosave', cwd=parent)
        run('git push origin', cwd=parent)

    @classmethod
    def prepare(cls, site_config):
        repo = site_config.get('repo', None)
        gitlab = site_config.get('gitlab', None)
        if repo is None:
            if gitlab is None:
                raise ValueError('repo/gitlab site config values not found')
            repo = 'git@{host}:{namespace}/{project}.git'.format(**gitlab)
        site_config.data['repo'] = repo
        return site_config


class GitLab:
    DEFAULT_API_VERSION = 'v4'

    def __init__(self, options):
        self.options = options
        self.options.setdefault('api_version', self.DEFAULT_API_VERSION)

    @cached_property
    def repo_url(self):
        return '{scheme}://{host}/api/{api_version}'.format(**self.options)

    @cached_property
    def path(self):
        return '{namespace}/{project}'.format(**self.options)

    @cached_property
    def namespace_id(self):
        namespace_name = self.options['namespace']
        response = requests.get(
            '{repo_url}/namespaces'.format(repo_url=self.repo_url),
            params={'search': namespace_name},
            headers=self.headers,
        )
        response.raise_for_status()
        namespaces = response.json()
        return one(x for x in namespaces if x['name'] == namespace_name)['id']

    def init_project(self):
        if self.path in (x['path_with_namespace'] for x in self.projects):
            raise Exception(f'Project {self.path} already exists')

        for item in ('projects', 'project_id'):
            if item in self.__dict__:
                del self.__dict__[item]

        response = requests.post(
            '{repo_url}/projects'.format(repo_url=self.repo_url),
            params={
                'name': self.options['project'],
                'namespace_id': self.namespace_id,
                'visibility': 'private',
                'default_branch': self.options['branch'],
                'tag_list': 'lectorium',
                'shared_runners_enabled': 'true',
            },
            headers=self.headers,
        )
        response.raise_for_status()
        ssh_repo_url = response.json()['ssh_url_to_repo']

        response = requests.post(
            '{repo_url}/projects/{pid}/variables'.format(
                repo_url=self.repo_url,
                pid=self.project_id,
            ),
            params={
                'id': self.project_id,
                'variable_type': 'file',
                'key': 'AWS_SHARED_CREDENTIALS_FILE',
                'value': AWS_SHARED_CREDENTIALS_FILE_TEMPLATE.format(
                    aws_key_id=environ['AWS_ACCESS_KEY_ID'],
                    aws_secret_key=environ['AWS_SECRET_ACCESS_KEY'],
                ),
            },
            headers=self.headers,
        )
        response.raise_for_status()

        return ssh_repo_url

    @cached_property
    def projects(self):
        response = requests.get(
            '{scheme}://{host}/api/{api_version}/projects'.format(**self.options),
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    @cached_property
    def headers(self):
        return {'Authorization': 'Bearer {token}'.format(**self.options)}

    @cached_property
    def merge_requests(self):
        response = requests.get(
            '{scheme}://{host}/api/{api_version}/projects/{pid}/merge_requests'.format(
                **self.options,
                pid=self.project_id
            ),
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    @cached_property
    def project_id(self):
        path = '{namespace}/{project}'.format(**self.options)
        return one(x for x in self.projects if x['path_with_namespace'] == path)['id']

    def create_merge_request(self, source_branch, target_branch, title):
        response = requests.post(
            '{scheme}://{host}/api/{api_version}/projects/{pid}/merge_requests'.format(
                **self.options,
                pid=self.project_id,
            ),
            data=dict(
                source_branch=source_branch,
                target_branch=target_branch,
                title=title,
            ),
            headers=self.headers,
        )
        response.raise_for_status()


class GitStorage(FileStorageMixin, Storage):
    CONFIG_CLASS = GitConfig

    def __init__(self, git):
        self.git = git
        self.workdir = pathlib.Path(closer(tempfile.TemporaryDirectory()))
        self.root = self.workdir / 'lektorium'
        self.root.mkdir()
        run(f'git clone {self.git} .', cwd=self.root)

    @staticmethod
    def init(path):
        lektorium = (path / 'lektorium')
        lektorium.mkdir(parents=True, exist_ok=True)
        run(f'git init --bare .', cwd=lektorium)
        return lektorium

    def create_session(self, site_id, session_id, session_dir):
        repo = self.config[site_id].get('repo', None)
        if repo is None:
            raise ValueError('site repo not found')
        branch = self.config[site_id].get('branch', '')
        if branch:
            branch = f'-b {branch}'
        run(f'git clone {repo} {branch} {session_dir}')
        run_local = functools.partial(run, cwd=session_dir)
        run_local(f'git checkout -b session-{session_id}')
        run_local(f'git push --set-upstream origin session-{session_id}')

    def create_site(self, lektor, name, owner, site_id):
        site_workdir = self.workdir / site_id
        if site_workdir.exists():
            raise ValueError('workdir for such site-id already exists')

        site_repo = self.create_site_repo(site_id)
        lektor.quickstart(name, owner, site_workdir)
        run_local = functools.partial(run, cwd=site_workdir)
        run_local('git init')
        run_local(f'git remote add origin {site_repo}')
        run_local('git fetch')
        run_local('git reset origin/master')
        run_local('git add .')
        run_local('git commit -m quickstart')
        run_local('git push --set-upstream origin master')

        return site_workdir, dict(repo=str(site_repo))

    def create_site_repo(self, site_id):
        site_repo = self.git.parent / site_id
        if site_repo.exists():
            raise ValueError('repo for such site-id already exists')

        site_repo.mkdir()
        run('git init --bare .', cwd=site_repo)
        with tempfile.TemporaryDirectory() as workdir:
            run_local = functools.partial(run, cwd=workdir)
            run_local(f'git clone {site_repo} .')
            run_local('git commit -m initial --allow-empty')
            run_local('git push')

        return site_repo

    def request_release(self, site_id, session_id, session_dir):
        run_local = functools.partial(run, cwd=session_dir)
        run_local('git add -A .')
        run_local('git commit -m autosave')
        run_local('git push')
        site = self.config[site_id]
        session = site.sessions[session_id]
        title_template = 'Request from: "{custodian}" <{custodian_email}>'
        return GitLab(site['gitlab']).create_merge_request(
            source_branch=f'session-{session_id}',
            target_branch=site.get('branch', 'master'),
            title=title_template.format(**session),
        )

    def get_merge_requests(self, site_id):
        site = self.config[site_id]
        gitlab_options = site.get('gitlab', None)
        if not gitlab_options:
            logging.warn('get_merge_requests: empty gitlab options')
            return []
        return GitLab(gitlab_options).merge_requests

    def site_config(self, site_id):
        return collections.defaultdict(type(None))

    def __repr__(self):
        name = self.__class__.__name__
        return f'{name}("{str(self.git)}"@"{str(self.root)}")'
