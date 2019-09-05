from os import sep, unlink
from tempfile import NamedTemporaryFile
from os.path import isdir
import pytest
import legit


@pytest.fixture(scope='module')
def tmpdir_gen(request, tmp_path_factory):
    from _pytest.tmpdir import _mk_tmp
    import py
    return lambda: py.path.local(_mk_tmp(request, tmp_path_factory))


def test_initialization(tmpdir):
    repository = legit.Repository(tmpdir)
    repo = repository.repo
    assert isdir(repo.working_tree_dir)
    assert repo.git_dir.startswith(repo.working_tree_dir)


def test_initialization_dot_attr(tmpdir):
    repository = legit.Repository.init(tmpdir)
    repo = repository.repo
    assert isdir(repo.working_tree_dir)
    assert repo.git_dir.startswith(repo.working_tree_dir)


def test_clone_into_empty_dir(tmpdir_gen):
    tmp_url = tmpdir_gen()
    tmp_path = tmpdir_gen()
    origin = legit.Repository.init(tmp_url)
    cloned_repo = origin.clone(url = tmp_url.strpath, path = tmp_path.strpath)
    assert cloned_repo.__class__ is legit.Repository
    assert isdir(cloned_repo.repo.working_tree_dir)
    assert cloned_repo.repo.git_dir.startswith(cloned_repo.repo.working_tree_dir)


def test_clone_into_non_empty_dir(tmpdir_gen):
    tmp_from = tmpdir_gen()
    tmp_into = tmpdir_gen()
    legit.Repository.init(tmp_into)
    clone_from = legit.Repository.init(tmp_from)
    new_clone = clone_from.clone(url = clone_from.repo.working_tree_dir, path = tmp_into.strpath)
    assert new_clone is None


def test_checkout(tmpdir):
    repo = legit.Repository.init(tmpdir)
    repo.checkout('branch_name')
    current_branch = repo.repo.active_branch.name
    assert current_branch == 'branch_name'


def test_add_file_and_commit(tmpdir):
    repo = legit.Repository.init(tmpdir)
    tmpfile1 = NamedTemporaryFile(dir=tmpdir, delete=False)
    tmpfile2 = NamedTemporaryFile(dir=tmpdir, delete=False)
    tmpname1 = tmpfile1.name.split(sep)[-1]
    tmpname2 = tmpfile2.name.split(sep)[-1]
    assert len(repo.repo.untracked_files) == 2
    assert tmpname1 in repo.repo.untracked_files
    assert tmpname2 in repo.repo.untracked_files
    repo.add_changes(files=[tmpname1])
    assert len(repo.repo.untracked_files) == 1
    assert list(repo.repo.index.entries.keys())[0][0] == tmpname1
    tmpfile1.close()
    unlink(tmpfile1.name)
    tmpfile2.close()
    unlink(tmpfile2.name)

def test_merge(tmpdir):
    repo = legit.Repository.init(tmpdir)
    tmpfile0 = NamedTemporaryFile(dir=tmpdir, delete=False)
    tmpfile0.close()
    tmpname0 = tmpfile0.name.split(sep)[-1]
    repo.add_changes(files=[tmpname0])
    repo.commit('message0')
    repo.checkout('branch_name')
    tmpfile1 = NamedTemporaryFile(dir=tmpdir, delete=False)
    tmpfile1.close()
    tmpname1 = tmpfile1.name.split(sep)[-1]
    repo.add_changes(files=[tmpname1])
    repo.commit('message')
    repo.checkout('master')
    repo.merge_branch('branch_name','master','msg')
    assert True == True




