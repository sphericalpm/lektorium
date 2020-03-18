import copy
import pytest
import respx
from lektorium.repo import (
    DuplicateEditSession,
    InvalidSessionState,
    ListRepo,
    SessionNotFound,
    SITES,
)
from lektorium.repo.local import FileStorage, GitStorage
from conftest import local_repo, git_repo
from lektorium.repo.memory import VALID_MERGE_REQUEST


def memory_repo(_):
    return ListRepo(copy.deepcopy(SITES))


@pytest.fixture(scope='function', params=[memory_repo, local_repo, git_repo])
def repo(request, tmpdir):
    return request.param(tmpdir)


def test_site_attributes(repo):
    attributes = set({a: s[a] for s in repo.sites for a in s})
    assert attributes.issuperset({
        'custodian',
        'custodian_email',
        'production_url',
        'sessions',
        'site_id',
        'site_name',
        'staging_url',
    })


def test_session_attributes(repo):
    repo.park_session(repo.create_session('uci'))
    repo.create_session('uci')
    attributes = set(a for s, _ in repo.sessions.values() for a in s)
    assert attributes == {
        'creation_time',
        'custodian',
        'custodian_email',
        'edit_url',
        'parked_time',
        'session_id',
        'view_url',
    }


def test_create_session(repo):
    sesison_before = len(list(repo.sessions))
    assert isinstance(repo.create_session('uci'), str)
    assert len(list(repo.sessions)) == sesison_before + 1


def test_create_session_other_exist(repo):
    assert isinstance(repo.create_session('uci'), str)
    with pytest.raises(DuplicateEditSession):
        repo.create_session('uci')


def test_destroy_session(repo):
    repo.create_session('uci')
    session_count_before = len(list(repo.sessions))
    repo.destroy_session(list(repo.sessions)[0])
    assert len(list(repo.sessions)) == session_count_before - 1


def test_destroy_unknown_session(repo):
    with pytest.raises(SessionNotFound):
        repo.destroy_session('test12345')


def test_park_session(repo):
    session_id = repo.create_session('uci')
    session_count_before = len(list(repo.parked_sessions))
    repo.park_session(session_id)
    assert len(list(repo.parked_sessions)) == session_count_before + 1


def test_park_unknown_session(repo):
    with pytest.raises(SessionNotFound):
        repo.park_session('test12345')


def test_park_parked_session(repo):
    session_id = repo.create_session('uci')
    repo.park_session(session_id)
    with pytest.raises(InvalidSessionState):
        repo.park_session(session_id)


def test_unpark_session(repo):
    session_id = repo.create_session('uci')
    repo.park_session(session_id)
    session_count_before = len(list(repo.parked_sessions))
    repo.unpark_session(session_id)
    assert len(list(repo.parked_sessions)) == session_count_before - 1


def test_unpark_session_another_exist(repo):
    session_id = repo.create_session('uci')
    repo.park_session(session_id)
    repo.create_session('uci')
    with pytest.raises(DuplicateEditSession):
        repo.unpark_session(session_id)


def test_unpark_unknown_session(repo):
    with pytest.raises(SessionNotFound):
        repo.unpark_session('test12345')


def test_unpark_unkparked_session(repo):
    session_id = repo.create_session('uci')
    with pytest.raises(InvalidSessionState):
        repo.unpark_session(session_id)


def test_sessions_in_site(repo):
    site = {x['site_id']: x for x in repo.sites}['uci']
    session_count_before = len(site['sessions'])
    session_id = repo.create_session('uci')
    assert len(site['sessions']) == session_count_before + 1
    repo.destroy_session(session_id)
    assert len(site['sessions']) == session_count_before


@pytest.mark.asyncio
async def test_create_site(repo):
    site_count_before = len(list(repo.sites))
    await repo.create_site('cri', 'Common Redundant Idioms')
    assert len(list(repo.sites)) == site_count_before + 1


@pytest.mark.asyncio
@respx.mock
async def test_releasing(repo, merge_requests):
    result = [item async for item in repo.releasing()]
    request = {
        'site_name': 'Buy Our Widgets',
        **VALID_MERGE_REQUEST,
    }
    if isinstance(getattr(repo, 'storage', None), (FileStorage, GitStorage)):
        return
    assert result == [request]


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_request_release(repo):
    session_id = repo.create_session('uci')
    await repo.request_release(session_id)
