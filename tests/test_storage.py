import collections
import os
import shutil
import pathlib
import pytest
from lektorium.repo.local.objects import Site
from lektorium.repo.local import FileStorage, GitStorage, LocalLektor
import requests_mock
from conftest import git_prepare


@pytest.fixture(
    scope='function',
    params=[
        FileStorage,
        git_prepare(GitStorage)
    ]
)
def storage_factory(request):
    return request.param


def test_everything(tmpdir, storage_factory):
    storage = storage_factory(tmpdir)
    assert isinstance(storage.config, dict)
    site_id = 'test-site'
    path, options = storage.create_site(
        LocalLektor,
        'Site Name',
        'Site Owner',
        site_id,
    )
    assert path.exists()
    storage.site_config(site_id).get('project.name')
    storage.config[site_id] = Site(site_id, None, **options)
    storage = storage_factory(tmpdir)
    assert len(storage.config)
    session_dir = tmpdir / 'session-id'
    assert not session_dir.exists()
    storage.create_session(site_id, 'session-id', session_dir)
    assert len(session_dir.listdir())
    if (tmpdir / site_id).exists():
        shutil.rmtree(tmpdir / site_id)
        storage.site_config(site_id).get('project.name')


def test_request_release(tmpdir):
    site_id, storage = 'site-id', git_prepare(GitStorage)(tmpdir)
    path, options = storage.create_site(LocalLektor, 's', 'o', site_id)
    storage.config[site_id] = Site(site_id, None, **options)
    session_id = 'session-id'
    session_dir = tmpdir / session_id
    storage.create_session(site_id, session_id, session_dir)
    page = (pathlib.Path(session_dir) / 'content' / 'contents.lr')
    page.write_text(os.linesep.join((page.read_text(), 'Signature.')))
    site = storage.config[site_id]
    site.sessions[session_id] = dict(custodian='user', custodian_email='email')
    site.data['gitlab'] = dict(
        scheme='https',
        host='server',
        namespace='user',
        project='project',
        token='token',
    )
    storage.config[site_id] = site
    with requests_mock.Mocker() as m:
        projects = [{'id': 123, 'path_with_namespace': 'user/project'}]
        m.get('https://server/api/v4/projects', json=projects)
        m.post('https://server/api/v4/projects/123/merge_requests')
        storage.request_release(site_id, session_id, session_dir)


CONFIG = '''
patrushev.me:
  branch: src
  email: apatrushev@gmail.com
  owner: Anton Patrushev
  repo: git@gitlab:apatrushev/apatrushev.github.io.git
  url: https://patrushev.me
spherical-website:
  email: mv@spherical.pm
  gitlab:
    host: gitlab
    namespace: apatrushev
    project: spherical-website
  owner: Michael Vartanyan
'''.lstrip()


def test_config_gitlab_repo(tmpdir):
    storage = git_prepare(GitStorage)(tmpdir)
    storage._config_path.write_text(CONFIG)

    def site_config_getter(_):
        return collections.defaultdict(type(None))

    config = GitStorage.load_config(storage._config_path, site_config_getter)
    site = config['spherical-website']
    gitlab_repo = site['repo']
    assert gitlab_repo == 'git@gitlab:apatrushev/spherical-website.git'
    assert site.sessions is not None
    config['spherical-website'] = config['spherical-website']
    assert CONFIG == storage._config_path.read_text()