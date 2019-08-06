from os.path import isdir
from tempfile import TemporaryDirectory, TemporaryFile

from git import Repo

import legit
import pytest


# import mockssh


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
    cloned_repo = origin.clone(tmp_path)
    assert cloned_repo.__class__ is Repo
    assert Repo.init(tmp_url).__class__ is Repo
    assert isdir(cloned_repo.working_tree_dir)
    assert cloned_repo.git_dir.startswith(cloned_repo.working_tree_dir)


def test_clone_into_non_empty_dir(tmpdir_gen):
    tmp_from = tmpdir_gen()
    tmp_into = tmpdir_gen()
    legit.Repository.init(tmp_into)
    clone_from = legit.Repository.init(tmp_from)
    new_clone = clone_from.clone(tmp_into)
    assert new_clone is None


# TODO: Rewrite
def test_checkout(tmpdir):
    repo = legit.Repository.init(tmpdir)
    new_branch = repo.checkout('branch_name')
    assert repo.active_branch == new_branch


# TODO: Rewrite
def test_add_file_and_commit(tmpdir):
    repo = legit.Repository.init(tmpdir)
    with TemporaryFile(dir=tmpdir) as tmpfilename:
        repo.add_changes(files=[tmpfilename])
    assert repo.commit == repo.active_branch.commit

# PLEASE DO NOT PUSH DEAD/COMMENTED-OUT CODE
# def test_push():
#     repository = legit.Repository.init(create_folder(folder)).repo
#     repo = legit.Repository.init(folder).repo
#     assert isdir(repository.working_tree_dir)
#     assert repository.git_dir.startswith(repository.working_tree_dir)
#     empty_repo = Repo.init(join(folder, 'empty'))
#     origin = empty_repo.create_remote('origin', repo.remotes.origin.url)
#     assert origin.exists()
#     assert origin ==
#             empty_repo.remotes.origin ==
#            empty_repo.remotes['origin']
#     # assure we actually have data. fetch() returns useful information
#     origin.fetch()
#     # Setup a local tracking branch of a remote branch
#     # create local branch "master" from remote "master"
#     empty_repo.create_head('master', origin.refs.master)
#     # set local "master" to track remote "master
#     empty_repo.heads.master.set_tracking_branch(origin.refs.master)
#     # checkout local "master" to working tree
#     empty_repo.heads.master.checkout()
#     empty_repo.create_head('master', origin.refs.master)
#                      .set_tracking_branch(origin.refs.master).checkout()
#     # rename remotes
#     origin.rename('new_origin')
#     origin.pull()
#     origin.push()
#     # create and delete remotes
#     assert not empty_repo.delete_remote(origin).exists()
