import collections
import shutil
import pytest
from lektorium.repo.local.objects import Site
from lektorium.repo.local import FileStorage, GitStorage, LocalLektor
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
