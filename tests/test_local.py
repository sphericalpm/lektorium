import pytest
from lektorium.repo import LocalRepo
from lektorium.repo.local import FakeServer, FakeLektor


@pytest.fixture
def repo(tmpdir):
    repo = LocalRepo(tmpdir, FakeServer(), FakeLektor)
    repo.create_site('bow', 'Buy Our Widgets')
    return repo


def test_fake_server():
    server = FakeServer()
    assert server.serve_lektor('/tmp')
    with pytest.raises(RuntimeError):
        assert server.serve_lektor('/tmp')
    server.stop_server('/tmp')
    assert server.serve_lektor('/tmp')


def test_create_site(tmpdir):
    repo = LocalRepo(tmpdir, FakeServer(), FakeLektor)
    assert not len(list(repo.root_dir.iterdir()))
    assert not len(list(repo.sites))
    repo.create_site('bow', 'Buy Our Widgets')
    assert len(list(repo.sites)) == 1
    repo = LocalRepo(tmpdir, FakeServer(), FakeLektor)
    assert len(list(repo.sites)) == 1


def test_session_create(repo):
    repo.create_session(next(repo.sites)['site_id'])
    assert len(list(repo.sessions)) == 1
