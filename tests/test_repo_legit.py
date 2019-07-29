from os.path import expanduser, isdir, exists, join, abspath, dirname
from os import makedirs, chmod, walk
from git import Repo
import sys
import legit
from shutil import rmtree
import unittest

url = 'https://github.com/katridi/test_folder.git'
folder = join(expanduser('~'), 'Desktop\\folder2')
path = abspath(dirname(dirname(abspath(__file__))))
sys.path.append(path)


def build_path(sub_dir: str) -> str:
    return join(expanduser('~'), f"Desktop\\{sub_dir}")


def create_folder(folder: str) -> str:
    if not exists(folder):
        makedirs(folder)
    assert isdir(folder)
    return folder


def change_mod_recursively(folder: str, permissions: oct = 0o777) -> None:
    for root, dirs, files in walk(folder):
        for d in dirs:
            chmod(join(root, d), permissions)
        for f in files:
            chmod(join(root, f), permissions)


def clean_folders(*args):
    for arg in args:
        if isdir(arg):
            change_mod_recursively(arg)
            rmtree(arg)


def clean_and_create(folder:str):
    clean_folders(folder)
    return create_folder(folder)


class TestGitMethods(unittest.TestCase):

    def tearDown(self):
        import gc
        gc.collect()

    def test_some(self):
        r = create_folder('./123')
        clean_folders(r)

    def test_initialization(self):
        clean_folders(folder)
        repository = legit.Repository(create_folder(folder))
        repo = repository.repo
        assert isdir(repo.working_tree_dir)
        assert repo.git_dir.startswith(repo.working_tree_dir)

    def test_initialization_dot_attr(self):
        clean_folders(folder)
        repository = legit.Repository.init(create_folder(folder))
        repo = repository.repo
        assert isdir(repo.working_tree_dir)
        assert repo.git_dir.startswith(repo.working_tree_dir)

    def test_cloning_empty_dir(self):
        clean_folders(folder)
        repository = legit.Repository(create_folder(folder)).repo
        repo = Repo(repository.working_tree_dir)
        cloned_repo = repo.clone(clean_and_create(build_path('newrepo')))  # TODO Check?
        # clone an existing repository
        assert cloned_repo.__class__ is Repo
        assert Repo.init(folder).__class__ is Repo
        # directory with your work files
        assert isdir(cloned_repo.working_tree_dir)
        # directory containing the git repository
        assert cloned_repo.git_dir.startswith(cloned_repo.working_tree_dir)

    def test_cloning_non_empty_dir(self):
        cloned_repo = legit.Repository.clone(url, clean_and_create(build_path('newrepo')))  # TODO Check?
        # no working tree
        git_path = build_path('newrepo\\.git')
        assert isdir(git_path)
        self.assertEqual(git_path, cloned_repo.repo.git_dir)

    def test_branching(self):
        cloned_repo = legit.Repository.clone(url, clean_and_create(build_path('newrepo'))).repo  # TODO Check?
        # create a new branch
        new_branch = cloned_repo.create_head('feature')
        # which wasn't checked out yet
        assert cloned_repo.active_branch != new_branch

    def test_commiting(self):
        cloned_repo = legit.Repository.clone(url, clean_and_create(build_path('newrepo'))).repo  # TODO Check?
        new_branch = cloned_repo.create_head('another-branch')
        assert cloned_repo.active_branch != new_branch
        # pointing to the checked-out commit
        self.assertEqual(new_branch.commit, cloned_repo.active_branch.commit)
        assert new_branch.set_commit('HEAD~1').commit == cloned_repo.active_branch.commit.parents[0]

    def test_add_file_and_commit(self):
        file_name = join(folder, 'new-file')
        r = legit.Repository.init(folder).repo
        # This function just creates an empty file
        open(file_name, 'wb').close()
        r.index.add([file_name])
        r.index.commit("initial commit")

    def test_push(self):
        repository = legit.Repository.init(create_folder(folder)).repo
        repo = legit.Repository.init(folder).repo
        assert isdir(repository.working_tree_dir)
        assert repository.git_dir.startswith(repository.working_tree_dir)
        empty_repo = Repo.init(join(folder, 'empty'))
        origin = empty_repo.create_remote('origin', repo.remotes.origin.url)
        assert origin.exists()
        assert origin == empty_repo.remotes.origin == empty_repo.remotes['origin']
        # assure we actually have data. fetch() returns useful information
        origin.fetch()
        # Setup a local tracking branch of a remote branch
        # create local branch "master" from remote "master"
        empty_repo.create_head('master', origin.refs.master)
        # set local "master" to track remote "master
        empty_repo.heads.master.set_tracking_branch(origin.refs.master)
        # checkout local "master" to working tree
        empty_repo.heads.master.checkout()
        empty_repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
        # rename remotes
        origin.rename('new_origin')
        origin.pull()
        origin.push()
        # create and delete remotes
        assert not empty_repo.delete_remote(origin).exists()
