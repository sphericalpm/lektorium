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
