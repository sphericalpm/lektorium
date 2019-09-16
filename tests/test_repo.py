import copy
import os
import pathlib
import pytest
import lektorium.repo


def local_repo(root_dir):
    repo = lektorium.repo.LocalRepo(root_dir)
    repo.create_site('bow', 'Buy Our Widgets')
    repo.create_site('uci', 'Underpants Collectors International')
    return repo


def memory_repo(_):
    return lektorium.repo.ListRepo(
        copy.deepcopy(lektorium.repo.SITES)
    )


@pytest.fixture(scope='function', params=[
    memory_repo,
    pytest.param(
        local_repo,
        marks=[
            pytest.mark.xfail(
                bool(int(os.environ.get('PYTEST_NOXFAIL', True))),
                reason='local repo is not fully implemented',
            )
        ]
    )
])
def repo(request, tmpdir):
    return request.param(tmpdir)


def test_site_attributes(repo):
    attributes = set(a for s in repo.sites for a in s)
    assert attributes == {
        'custodian',
        'custodian_email',
        'production_url',
        'sessions',
        'site_id',
        'site_name',
        'staging_url',
    }


def test_session_attributes(repo):
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
    with pytest.raises(lektorium.repo.DuplicateEditSession):
        repo.create_session('uci')


def test_destroy_session(repo):
    assert len(list(repo.sessions)) == 3
    repo.destroy_session('pantss1')
    assert len(list(repo.sessions)) == 2


def test_destroy_unknown_session(repo):
    with pytest.raises(lektorium.repo.SessionNotFound):
        repo.destroy_session('test12345')


def test_park_session(repo):
    assert len(list(repo.parked_sessions)) == 2
    repo.park_session('widgets-1')
    assert len(list(repo.parked_sessions)) == 3


def test_park_unknown_session(repo):
    with pytest.raises(lektorium.repo.SessionNotFound):
        repo.park_session('test12345')


def test_park_parked_session(repo):
    repo.park_session('widgets-1')
    with pytest.raises(lektorium.repo.InvalidSessionState):
        repo.park_session('widgets-1')


def test_unpark_session(repo):
    assert len(list(repo.parked_sessions)) == 2
    repo.unpark_session('pantssss')
    assert len(list(repo.parked_sessions)) == 1


def test_unpark_session_another_exist(repo):
    repo.unpark_session('pantssss')
    with pytest.raises(lektorium.repo.DuplicateEditSession):
        repo.unpark_session('pantss1')


def test_unpark_unknown_session(repo):
    with pytest.raises(lektorium.repo.SessionNotFound):
        repo.unpark_session('test12345')


def test_unpark_unkparked_session(repo):
    with pytest.raises(lektorium.repo.InvalidSessionState):
        repo.unpark_session('widgets-1')
