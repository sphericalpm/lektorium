from os.path import isdir
from tempfile import TemporaryDirectory, TemporaryFile

from git import Repo

import legit

# TODO: Consider @fixture for cloning and stuff like that


def test_initialization():
    with TemporaryDirectory() as tmpdirname:
        repository = legit.Repository(tmpdirname)
        repo = repository.repo
        assert isdir(repo.working_tree_dir)
        assert repo.git_dir.startswith(repo.working_tree_dir)


def test_initialization_dot_attr():
    with TemporaryDirectory() as tmpdirname:
        repository = legit.Repository.init(tmpdirname)
        repo = repository.repo
        assert isdir(repo.working_tree_dir)
        assert repo.git_dir.startswith(repo.working_tree_dir)


def test_clone_into_empty_dir():
    with TemporaryDirectory() as tmp_url, TemporaryDirectory() as tmp_path:
        origin = legit.Repository.init(tmp_url)
        cloned_repo = origin.clone(tmp_path)
        assert cloned_repo.__class__ is Repo
        assert Repo.init(tmp_url).__class__ is Repo
        assert isdir(cloned_repo.working_tree_dir)
        assert cloned_repo.git_dir.startswith(cloned_repo.working_tree_dir)


def test_clone_into_non_empty_dir():
    with TemporaryDirectory() as tmp_from, TemporaryDirectory() as tmp_into:
        legit.Repository.init(tmp_into)
        clone_from = legit.Repository.init(tmp_from)
        new_clone = clone_from.clone(tmp_into)
        assert new_clone is None

# TODO: Rewrite
def test_checkout():
    with TemporaryDirectory() as tmpdirname:
        repo = legit.Repository.init(tmpdirname)
        new_branch = repo.checkout('branch_name')
        assert repo.active_branch == new_branch

# TODO: Rewrite
def test_add_file_and_commit():
    with TemporaryDirectory() as tmpdirname:
        repo = legit.Repository.init(tmpdirname)
        with TemporaryFile(dir=tmpdirname) as tmpfilename:
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
