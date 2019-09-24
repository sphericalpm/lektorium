import pytest
import unittest.mock
from lektorium.repo import LocalRepo
from lektorium.repo.local import FakeServer, FakeLektor
from lektorium.repo.local.repo import Site, Session


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
    server = unittest.mock.Mock()
    server.serve_static.assert_not_called()
    repo = LocalRepo(tmpdir, server, FakeLektor)
    assert len(list(repo.sites)) == 1
    server.serve_static.assert_called_once()


def test_site_restrict_fields():
    restrict_props = {'sessions': [], 'staging_url': 'http://stag.test'}
    with pytest.raises(RuntimeError):
        assert Site('test_id', 'http://site.test', **(restrict_props))


def test_site_items():
    props = {'additional_prop': 'test'}

    def production_url():
        return 'http://stag.test', 'http://stag.test'

    site = Site('test_site', production_url, **(props))
    assert site['production_url'] == 'http://stag.test'


def test_site_len():
    site = Site('test_site', 'http://stag.test')
    assert len(site) == 4


def test_session():
    session = Session(session_name='test_session', edit_url='http://stag.test')
    assert len(session) == 2
    assert session.edit_url == 'http://stag.test'


def test_session_callable_editurl():
    def edit_url():
        return ('edit_url', 'http://stag.test')
    session = Session(session_name='test_session', edit_url=edit_url)
    assert session.edit_url == 'http://stag.test'


def test_session_create(repo):
    repo.create_session(next(repo.sites)['site_id'])
    assert len(list(repo.sessions)) == 1
