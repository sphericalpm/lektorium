import abc
import asyncio
import collections
import functools
import os
import pathlib
import shutil
import subprocess
import tempfile
from urllib.parse import quote_plus

import dateutil
import inifile
import requests
import unsync
import yaml
from cached_property import cached_property
from more_itertools import one, only

from ...aws import AWS
from ...utils import closer
from .objects import Site
from .templates import (
    AWS_SHARED_CREDENTIALS_FILE_TEMPLATE,
    EMPTY_COMMIT_PAYLOAD,
    GITLAB_CI_TEMPLATE,
    LECTOR_S3_SERVER_TEMPLATE,
)


LFS_MASKS = (
    '*.doc*',
    '*.xls*',
    '*.gif',
    '*.png',
    '*.svg',
    '*.jpeg',
    '*.webp',
    '*.pdf',
    '*.zip',
    '*.avi',
    '*.mov',
    '*.mp*',
    '*.webm',
    '*.ttf',
    '*.woff',
)
run = functools.partial(subprocess.check_call, shell=True)
run_out = functools.partial(subprocess.check_output, shell=True)


def async_run(func, *args, **kwargs):
    return asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(func, *args, **kwargs),
    )


class ConfigGetter:
    @staticmethod
    def directory_config(dir):
        config = only(dir.glob('*.lektorproject'))
        if config:
            return inifile.IniFile(config)
        return collections.defaultdict(type(None))

    def site_config(self, site_id):
        workdir = self._site_dir(site_id)
        return self.directory_config(workdir)


class Themer:
    @cached_property
    def theme_repos(self):
        return [
            item.strip() for item in
            os.environ.get('LEKTORIUM_LEKTOR_THEME', '').split(';')
        ]

    def themes(self, names=[]):
        repos_dict = self.make_theme_dict(self.theme_repos)
        repos = [repo for repo, name in repos_dict.items() if name in names]
        if repos:
            return self.make_theme_dict(repos)
        return repos_dict

    def sparce_repo_config(self, site_id):
        sparce_site_id = f'{site_id}-sparce-clone'
        dir = self._site_dir(sparce_site_id)
        run_local = functools.partial(run, cwd=dir)

        if dir.exists():
            shutil.rmtree(dir, ignore_errors=True)
        dir.mkdir()
        run_local('git init .')
        run_local(f'git remote add origin {self.config[site_id]["repo"]}')
        run_local('git config core.sparseCheckout true')
        run_local(f'echo "{site_id}.lektorproject" >> .git/info/sparse-checkout')
        run_local('git pull --depth=1 origin master')
        return self.site_config(sparce_site_id)

    def site_themes(self, site_id):
        config = self.site_config(site_id)
        if not config:
            config = self.sparce_repo_config(site_id)
        all_themes = self.themes().values()
        config_themes = [
            theme.strip() for theme in
            config.get('project.themes', '').split(',')
            if theme.strip() in all_themes
        ]

        themes = config_themes[:]
        for name in all_themes:
            if name not in themes:
                themes.append(name)

        all_active = False if config_themes else True
        themes = [
            {'name': name, 'active': True if all_active or name in config_themes else False}
            for name in themes
        ]
        return themes

    def repo_themes(self, repo_dir):
        theme_paths = run_out(
            'git config --file .gitmodules --name-only --get-regexp path | tee',
            cwd=repo_dir,
        )
        return [
            os.path.basename(item.lstrip('submodule.').rstrip('.path'))
            for item in theme_paths.decode().split()
            if item.startswith('submodule.themes/')
        ]

    @staticmethod
    def make_theme_dict(repos):
        themes = collections.OrderedDict()
        for repo in repos:
            themes[repo] = os.path.basename(repo).rstrip('.git')
        return themes

    def set_themes_config(self, dir, theme_names):
        config = self.directory_config(dir)
        if not theme_names:
            del config['project.themes']
        else:
            config['project.themes'] = ','.join(theme_names)
        config.save()

    async def set_theme_submodules(self, dir, new_themes):
        run_local = functools.partial(run_out, cwd=dir)
        existing_themes = []

        for theme_name in self.repo_themes(dir):
            if theme_name in new_themes.values():
                existing_themes.append(theme_name)
            else:
                await async_run(run_local, f'git rm "themes/{theme_name}"')

        for theme_repo, theme_name in new_themes.items():
            if theme_name not in existing_themes:
                await async_run(
                    run_local,
                    f'git submodule add --force {theme_repo} themes/{theme_name}',
                )

        self.set_themes_config(dir, new_themes.values())
        await async_run(run_local, 'git add -A .')
        await async_run(run_local, 'git diff-index --quiet HEAD || git commit -m "Update themes"')


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
    def create_session(self, site_id, session_id, session_dir, themes):
        """Creates new session.

        This method mades all mandatory actions to create new session in
        storage itself and fill session_dir with files to start lektor server
        to work on site content.
        """

    @abc.abstractmethod
    def update_session(self, site_id, session_id, session_dir):
        """Updates existing session.

        This method mades any actions to update existing session in
        session_dir but not in storage itself.
        """

    @abc.abstractmethod
    def save_session(self, site_id, session_id, session_dir):
        """Saves existing session.

        This method mades any actions to save existing session from
        session_dir to storage.
        """

    @abc.abstractmethod
    def create_site(self, lektor, name, owner, site_id, themes):
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

    @abc.abstractmethod
    def site_themes(self, site_id):
        """Returns a dict-like object with available themes.

        Returns a dict with theme repos as keys and theme names as values.
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
                sk != 'repo' or GitlabStorage.GITLAB_SECTION_NAME not in site_config.data
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
                    config_data = yaml.load(config_file, Loader=yaml.Loader) or {}
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

    def get_merge_requests(self, site_id):
        raise RuntimeError('no merge requests for this type of storage')

    @cached_property
    def config(self):
        return self.load_config(self._config_path, self.site_config)

    @property
    def _config_path(self):
        return self.root / self.CONFIG_FILENAME


class FileStorage(ConfigGetter, FileStorageMixin, Storage):
    CONFIG_CLASS = FileConfig

    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()

    def site_themes(self, *args, **kwargs):
        return []

    def create_session(self, site_id, session_id, session_dir, themes=None):
        site_root = self._site_dir(site_id)
        shutil.copytree(site_root, session_dir)

    def update_session(self, site_id, session_id, session_dir):
        pass

    def save_session(self, site_id, session_id, session_dir):
        pass

    async def create_site(self, lektor, name, owner, site_id, themes=None):
        site_root = self._site_dir(site_id)
        lektor.quickstart(name, owner, site_root)
        return site_root, {}

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
        run('git diff-index --quiet HEAD || git commit -m autosave', cwd=parent)
        run('git push origin', cwd=parent)

    @classmethod
    def prepare(cls, site_config):
        repo = site_config.get('repo', None)
        gitlab = site_config.get(GitlabStorage.GITLAB_SECTION_NAME, None)
        if repo is None:
            if gitlab is None:
                raise ValueError('repo/gitlab site config values not found')
            repo = 'git@{host}:{namespace}/{project}.git'.format(**gitlab)
        site_config.data['repo'] = repo
        return site_config


class GitLab:
    DEFAULT_API_VERSION = 'v4'
    AWS_CREDENTIALS_VARIABLE_NAME = 'AWS_SHARED_CREDENTIALS_FILE'
    BATCH_SIZE = 100

    def __init__(self, options):
        self.options = options
        self.options['encoded_namespace'] = quote_plus(options['namespace'])
        self.options.setdefault('api_version', self.DEFAULT_API_VERSION)

    @cached_property
    def repo_url(self):
        return '{scheme}://{host}/api/{api_version}'.format(**self.options)

    @property
    def skip_aws(self):
        return self.options.get('skip_aws', False)

    @cached_property
    def path(self):
        return '{namespace}/{project}'.format(**self.options)

    def lookup_parent_id(self, objects_type, path_attribute):
        response = requests.get(
            f'{self.repo_url}/{objects_type}',
            headers=self.headers,
        )
        response.raise_for_status()
        objects = [
            x for x in response.json()
            if x[path_attribute] == self.options['namespace']
        ]
        if objects:
            return one(objects)['id']
        return None

    @cached_property
    def namespace_id(self):
        parent_id = self.lookup_parent_id('groups', 'full_path')
        if parent_id is None:
            parent_id = self.lookup_parent_id('namespaces', 'path')
        if parent_id is None:
            raise RuntimeError('parent namespace and/or gorup is not found')
        return parent_id

    async def init_project(self):
        if self.path in (x['path_with_namespace'] for x in self.projects):
            raise Exception(f'Project {self.path} already exists')

        for item in ('projects', 'project_id'):
            if item in self.__dict__:
                del self.__dict__[item]

        ssh_repo_url = self._create_new_project().json()['ssh_url_to_repo']
        await asyncio.sleep(1)
        if not self.skip_aws:
            self._create_aws_project_variable()
        self._create_initial_commit()

        return ssh_repo_url

    def _create_new_project(self):
        response = requests.post(
            '{repo_url}/projects'.format(repo_url=self.repo_url),
            params={
                'name': self.options['project'],
                'namespace_id': self.namespace_id,
                'visibility': 'private',
                'default_branch': self.options['branch'],
                'tag_list': 'lektorium',
                'shared_runners_enabled': 'true',
                'lfs_enabled': 'true',
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response

    def _create_aws_project_variable(self):
        response = requests.post(
            '{repo_url}/projects/{pid}/variables'.format(
                repo_url=self.repo_url,
                pid=self.project_id,
            ),
            params={
                'id': self.project_id,
                'variable_type': 'file',
                'key': self.AWS_CREDENTIALS_VARIABLE_NAME,
                'value': AWS_SHARED_CREDENTIALS_FILE_TEMPLATE.format(
                    aws_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                    aws_secret_key=os.environ['AWS_SECRET_ACCESS_KEY'],
                ),
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response

    def _create_initial_commit(self):
        headers = dict(self.headers)
        headers.update({'Content-Type': 'application/json'})
        # Make initial empty commit in repository
        response = requests.post(
            '{repo_url}/projects/{pid}/repository/commits'.format(
                repo_url=self.repo_url,
                pid=self.project_id,
            ),
            data=EMPTY_COMMIT_PAYLOAD,
            headers=headers,
        )
        response.raise_for_status()
        return response

    @cached_property
    def projects(self):
        projects, page = [], 1
        while True:
            url = (
                '{scheme}://{host}/api/{api_version}/'
                'groups/{encoded_namespace}/projects'
            ).format(**self.options)
            response = requests.get(
                url,
                headers=self.headers,
                params=dict(simple=True, page=page, per_page=self.BATCH_SIZE),
            )
            response.raise_for_status()
            result = response.json()
            if not len(result):
                break
            projects.extend(result)
            page += 1
        return projects

    @cached_property
    def headers(self):
        return {'Authorization': 'Bearer {token}'.format(**self.options)}

    @cached_property
    def merge_requests(self):
        response = requests.get(
            '{scheme}://{host}/api/{api_version}/{scope}merge_requests'.format(
                scope=(
                    f'projects/{self.project_id}/'
                    if 'project' in self.options else
                    ''
                ),
                **self.options,
            ),
            headers=self.headers,
        )
        response.raise_for_status()
        result = response.json()
        for r in result:
            if 'created_at' in r:
                r['created_at'] = dateutil.parser.parse(r['created_at'])
        return result

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


class GitStorage(ConfigGetter, Themer, FileStorageMixin, Storage):
    CONFIG_CLASS = GitConfig

    def __init__(self, git):
        self.git = git
        self.workdir = pathlib.Path(closer(tempfile.TemporaryDirectory()))
        self.root = self.workdir / 'lektorium'
        self.root.mkdir()
        run(f'git clone {self.git} .', cwd=self.root)

    def _site_dir(self, site_id):
        return self.workdir / site_id

    @staticmethod
    def init(path):
        lektorium = (path / 'lektorium')
        lektorium.mkdir(parents=True, exist_ok=True)
        run('git init --bare .', cwd=lektorium)
        run('git symbolic-ref HEAD refs/heads/master', cwd=lektorium)
        return lektorium

    def create_session(self, site_id, session_id, session_dir, themes=None):
        repo = self.config[site_id].get('repo', None)
        if repo is None:
            raise ValueError('site repo not found')

        run_local = functools.partial(run, cwd=session_dir)

        branch = self.config[site_id].get('branch', '')
        if branch:
            branch = f'-b {branch}'
        run(f'git clone {repo} {branch} {session_dir}')
        self.check_theme_repos(session_dir)
        run_local('git submodule update --init --recursive')
        run_local(f'git checkout --recurse-submodules -b session-{session_id}')

        if themes is not None:
            set_fn = unsync.unsync()(self.set_theme_submodules)
            set_fn(session_dir, self.themes(themes)).result()

        run_local(f'git push --set-upstream origin session-{session_id}')
        run_local('git submodule update --remote')

    def update_session(self, site_id, session_id, session_dir):
        run_local = functools.partial(run, cwd=session_dir)
        run_local('git pull')
        self.check_theme_repos(session_dir)
        run_local('git submodule update --remote')

    def save_session(self, site_id, session_id, session_dir):
        run_local = functools.partial(run, cwd=session_dir)
        run_local('git add -A .')
        try:
            run_local('git diff --cached | grep .')
        except subprocess.CalledProcessError:
            return
        run_local('git commit -m autosave')
        run_local('git push')

    def check_theme_repos(self, repo_dir):
        run_local = functools.partial(run_out, cwd=repo_dir)
        themes = {v: k for k, v in self.themes().items()}
        for theme in self.repo_themes(repo_dir):
            if theme in themes:
                repo = run_local(f'git config --file .gitmodules submodule.themes/{theme}.url')
                if repo.decode().strip() != themes[theme]:
                    run_local(f'git rm "themes/{theme}"')
                    run_local(f'git submodule add --force {themes[theme]} themes/{theme}')
        run_local('git add -A .')
        run_local('git diff-index --quiet HEAD || git commit -m "Update theme repos"')

    async def create_site(self, lektor, name, owner, site_id, themes=None):
        site_workdir = self._site_dir(site_id)
        if site_workdir.exists():
            raise ValueError('workdir for such site-id already exists')

        run_local = functools.partial(run, cwd=site_workdir)

        site_repo = await self.create_site_repo(site_id)
        theme_repos = self.themes(themes)

        if theme_repos:
            example_site = None
            with tempfile.TemporaryDirectory() as theme_dir:
                for theme_repo, theme_name in theme_repos.items():
                    repo_tmp_dir = pathlib.Path(theme_dir) / theme_name
                    await async_run(run, f'git clone {theme_repo} {repo_tmp_dir}')
                    if (repo_tmp_dir / 'example-site').exists():
                        if example_site is not None:
                            raise ValueError('Only one example site must exists across theme repos')
                        example_site = repo_tmp_dir / 'example-site'
                if example_site is not None and example_site.exists():
                    shutil.rmtree(example_site / 'themes', ignore_errors=True)
                    shutil.copytree(example_site, site_workdir)
            site_config = self.site_config(site_id)
            if site_config:
                site_config['project.name'] = name
                del site_config['project.url']
                site_config.save()
                pathlib.Path(site_config.filename).rename(site_workdir / f'{name}.lektorproject')
            else:
                shutil.rmtree(site_workdir, ignore_errors=True)

        if not theme_repos or not site_workdir.exists():
            lektor.quickstart(name, owner, site_workdir)
            if not theme_repos:
                shutil.rmtree(site_workdir / 'templates')
                shutil.rmtree(site_workdir / 'models')

        await async_run(run_local, 'git init')
        await async_run(run_local, 'git symbolic-ref HEAD refs/heads/master')
        await async_run(run_local, 'git lfs install')
        await async_run(run_local, f'git remote add origin {site_repo}')
        await async_run(run_local, 'git fetch')
        await async_run(run_local, 'git reset origin/master')
        (site_workdir / '.gitattributes').write_text(
            os.linesep.join(
                f'{m} filter=lfs diff=lfs merge=lfs -text'
                for m in LFS_MASKS
            ),
        )

        await async_run(run_local, 'git add .')
        await async_run(run_local, 'git commit -m quickstart')

        if theme_repos:
            await self.set_theme_submodules(site_workdir, theme_repos)

        await async_run(run_local, 'git push --set-upstream origin master')

        return (
            site_workdir,
            dict(repo=str(site_repo), themes=list(theme_repos.values())),
        )

    async def create_site_repo(self, site_id):
        site_repo = self.git.parent / site_id
        if site_repo.exists():
            raise ValueError('repo for such site-id already exists')

        site_repo.mkdir()
        await async_run(run, 'git init --bare .', cwd=site_repo)
        await async_run(run, 'git symbolic-ref HEAD refs/heads/master', cwd=site_repo)
        with tempfile.TemporaryDirectory() as workdir:
            run_local = functools.partial(run, cwd=workdir)
            await async_run(run_local, f'git clone {site_repo} .')
            await async_run(run_local, 'git commit -m initial --allow-empty')
            await async_run(run_local, 'git push')

        return site_repo

    def request_release(self, site_id, session_id, session_dir):
        self.save_session(site_id, session_id, session_dir)

    def __repr__(self):
        name = self.__class__.__name__
        return f'{name}("{str(self.git)}"@"{str(self.root)}")'


class GitlabStorage(GitStorage):
    GITLAB_SECTION_NAME = 'gitlab'

    def __init__(self, git, token, protocol, skip_aws=False):
        super().__init__(git)
        git = str(git)
        self.token = token
        self.protocol = protocol
        self.skip_aws = skip_aws
        head, _, tail = git.partition('@')
        self.repo, _, path = tail.partition(':')
        self.namespace, _, _ = path.rpartition('/')

    def gitlab_options(self, **extra_options):
        return dict(
            scheme=self.protocol,
            host=self.repo,
            namespace=self.namespace,
            token=self.token,
            skip_aws=self.skip_aws,
            **extra_options,
        )

    @staticmethod
    def update_gitlab_ci(dir):
        with open(str(dir / '.gitlab-ci.yml'), 'w') as fo:
            fo.write(GITLAB_CI_TEMPLATE)

    async def create_site(self, lektor, name, owner, site_id, themes=None):
        site_workdir, options = await super().create_site(lektor, name, owner, site_id, themes)
        if not self.skip_aws:
            aws = AWS()
            bucket_name = aws.create_s3_bucket(site_id)
            aws.open_bucket_access(bucket_name)
            distribution_id, domain_name = aws.create_cloudfront_distribution(bucket_name)

            with open(str(site_workdir / f'{name}.lektorproject'), 'a') as fo:
                fo.write(LECTOR_S3_SERVER_TEMPLATE.format(
                    s3_bucket_name=bucket_name,
                    cloudfront_id=distribution_id,
                ))

            self.update_gitlab_ci(site_workdir)

            run_local = functools.partial(run, cwd=site_workdir)
            await async_run(run_local, 'git add .')
            await async_run(run_local, 'git commit -m "Add AWS deploy integration"')
            await async_run(run_local, 'git push --set-upstream origin master')

            options.update({
                'cloudfront_domain_name': domain_name,
                'url': f'https://{domain_name}',
            })

        return site_workdir, options

    def request_release(self, site_id, session_id, session_dir):
        self.update_gitlab_ci(session_dir)
        super().request_release(site_id, session_id, session_dir)
        site = self.config[site_id]
        session = site.sessions[session_id]
        title_template = 'Request from: "{custodian}" <{custodian_email}>'
        return self.gitlab(site_id).create_merge_request(
            source_branch=f'session-{session_id}',
            target_branch=site.get('branch', 'master'),
            title=title_template.format(**session),
        )

    @cached_property
    def merge_requests(self):
        return GitLab(self.gitlab_options()).merge_requests

    @cached_property
    def projects(self):
        gitlab = GitLab(self.gitlab_options())
        return {x['path_with_namespace']: x for x in gitlab.projects}

    def get_merge_requests(self, site_id):
        project_id = self.projects[f'{self.namespace}/{site_id}']['id']
        return [x for x in self.merge_requests if x['project_id'] == project_id]

    async def create_site_repo(self, site_id):
        return await self.gitlab(site_id).init_project()

    def gitlab(self, project, branch='master'):
        return GitLab(self.gitlab_options(
            project=project,
            branch=branch,
        ))
