import pytest
import asyncio
import unittest.mock
from lektorium.repo import LocalRepo
from lektorium.repo.local import (
    FakeLektor,
    FakeServer,
    FileStorage,
    LocalLektor,
)
from lektorium.repo.local.repo import Site, Session
from lektorium.utils import run_coroutine
from conftest import local_repo, git_repo


@pytest.fixture(scope='function', params=[local_repo, git_repo])
def repo(request, tmpdir):
    return request.param(tmpdir)


@pytest.mark.asyncio
async def test_fake_server():
    server = FakeServer()
    assert await server.serve_lektor('/tmp')
    with pytest.raises(RuntimeError):
        assert await server.serve_lektor('/tmp')
    await server.stop_server('/tmp')
    assert await server.serve_lektor('/tmp')


def test_create_site(tmpdir):
    repo = LocalRepo(FileStorage(tmpdir), FakeServer(), FakeLektor)
    assert not len(list(repo.storage.root.iterdir()))
    assert not len(list(repo.sites))
    run_coroutine(repo.create_site('bow', 'Buy Our Widgets'))
    assert len(list(repo.sites)) == 1
    server = unittest.mock.AsyncMock()
    server.serve_static.assert_not_called()
    repo = LocalRepo(FileStorage(tmpdir), server, FakeLektor)
    assert len(list(repo.sites)) == 1
    server.serve_static.assert_called_once()


def test_site_restrict_fields():
    restrict_props = {'sessions': [], 'staging_url': 'http://stag.test'}
    with pytest.raises(ValueError):
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


@pytest.mark.asyncio
async def test_session_create(repo):
    await repo.create_session(next(repo.sites)['site_id'])
    assert len(list(repo.sessions)) == 1


def test_lektor_config_loading(tmpdir):
    repo = LocalRepo(FileStorage(tmpdir), FakeServer(), LocalLektor)
    run_coroutine(repo.create_site('a', 'b'))
    LocalRepo(FileStorage(tmpdir), FakeServer(), LocalLektor)
