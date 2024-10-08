import collections
import os
import pathlib
import shutil

import pytest
import requests_mock
from conftest import git_prepare

from lektorium.repo.local import (
    FileStorage,
    GitlabStorage,
    GitStorage,
    LocalLektor,
)
from lektorium.repo.local.objects import Site


@pytest.fixture(
    scope='function',
    params=[
        FileStorage,
        git_prepare(GitStorage),
    ],
)
def storage_factory(request):
    return request.param


@pytest.mark.asyncio
async def test_everything(tmpdir, storage_factory):
    storage = storage_factory(tmpdir)
    assert isinstance(storage.config, dict)
    site_id = 'test-site'
    path, options = await storage.create_site(
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


@pytest.mark.skip(reason='too wide test')
@pytest.mark.asyncio
async def test_request_release(tmpdir):
    site_id, storage = 'site-id', git_prepare(GitStorage)(tmpdir)
    path, options = await storage.create_site(LocalLektor, 's', 'o', site_id)
    storage.config[site_id] = Site(site_id, None, **options)
    session_id = 'session-id'
    session_dir = tmpdir / session_id
    storage.create_session(site_id, session_id, session_dir)
    page = (pathlib.Path(session_dir) / 'content' / 'contents.lr')
    page.write_text(os.linesep.join((page.read_text(), 'Signature.')))
    site = storage.config[site_id]
    site.sessions[session_id] = dict(custodian='user', custodian_email='email')
    site.data[GitlabStorage.GITLAB_SECTION_NAME] = dict(
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
        post_url = 'https://server/api/v4/projects/123/merge_requests'
        m.post(post_url)
        storage.request_release(site_id, session_id, session_dir)
        assert m.call_count == 2
        last_request = m.request_history[-1]
        assert last_request.url == post_url
        assert last_request.method == 'POST'
        assert last_request.body == (
            'source_branch=session-session-id&'
            'target_branch=master&'
            'title=Request+from%3A+%22user%22+%3Cemail%3E'
        )


@pytest.mark.skip(reason='too wide test')
@pytest.mark.asyncio
async def test_get_merge_requests(tmpdir, merge_requests):
    site_id, storage = 'site-id', git_prepare(GitStorage)(tmpdir)
    path, options = await storage.create_site(LocalLektor, 's', 'o', site_id)
    storage.config[site_id] = Site(site_id, None, **options)
    site = storage.config[site_id]
    site.data[GitlabStorage.GITLAB_SECTION_NAME] = dict(
        scheme='https',
        host='server',
        namespace='user',
        project='project',
        token='token',
    )
    storage.config[site_id] = site
    result = storage.get_merge_requests(site_id)
    assert result == merge_requests


CONFIG = '''
company-website:
  email: mv@company.pm
  gitlab:
    host: gitlab
    namespace: user
    project: company-website
  owner: Muser Museryan
site.url:
  branch: src
  email: user@example.com
  owner: User Userovich
  repo: git@gitlab:user/site.repo.git
  url: https://site.url
'''.lstrip()


def test_config_gitlab_repo(tmpdir):
    storage = git_prepare(GitStorage)(tmpdir)
    storage._config_path.write_text(CONFIG)

    def site_config_getter(_):
        return collections.defaultdict(type(None))

    config = GitStorage.load_config(storage._config_path, site_config_getter)
    site = config['company-website']
    gitlab_repo = site['repo']
    assert gitlab_repo == 'git@gitlab:user/company-website.git'
    assert site.sessions is not None
    config['company-website'] = config['company-website']
    assert CONFIG == storage._config_path.read_text()
