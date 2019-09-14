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
