import pytest
from lektorium.repo import LocalRepo
from lektorium.repo.local import FakeServer


def test_fake_server():
    server = FakeServer()
    assert server.serve_lektor('/tmp')
    with pytest.raises(RuntimeError):
        assert server.serve_lektor('/tmp')
    server.stop_server('/tmp')
    assert server.serve_lektor('/tmp')


def test_create_site(tmpdir):
    repo = LocalRepo(tmpdir, FakeServer())
    assert not len(list(repo.root_dir.iterdir()))
    assert not len(list(repo.sites))
    repo.create_site('bow', 'Buy Our Widgets')
    assert len(list(repo.sites)) == 1
    repo = LocalRepo(tmpdir, FakeServer())
    assert len(list(repo.sites)) == 1
