import copy
import pytest
import lektorium.repo


@pytest.fixture
def repo():
    return lektorium.repo.ListRepo(
        copy.deepcopy(lektorium.repo.SITES)
    )


def test_create_session(repo):
    assert len(list(repo.sessions)) == 3
    repo.create_session('uci')
    assert len(list(repo.sessions)) == 4


def test_create_session_other_exist(repo):
    with pytest.raises(lektorium.repo.DuplicateEditSession):
        repo.create_session('bow')


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
    with pytest.raises(lektorium.repo.SessionAlreadyParked):
        repo.park_session('widgets-1')
