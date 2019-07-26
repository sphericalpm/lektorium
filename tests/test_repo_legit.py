from os.path import expanduser, isdir, exists, join, abspath, dirname
from os import makedirs, chmod, walk
from git import Repo
import sys
import legit
from shutil import rmtree
import unittest


url = 'https://github.com/katridi/test_folder'
folder = join(expanduser('~'), 'Desktop\\folder2')
path = abspath(dirname(dirname(abspath(__file__))))
sys.path.append(path)


def create_folder(folder: str) -> str:
    if not exists(folder):
        makedirs(folder)
    assert isdir(folder)


class TestGitMethods(unittest.TestCase):

    def tearDown(self):
        import gc
        gc.collect()

    def change_mod_recursively(fodler: str, permissions: oct = 0o777) -> None:
        for root, dirs, files in walk(folder):
            for d in dirs:
                chmod(join(root, d), permissions)
            for f in files:
                chmod(join(root, f), permissions)

    def test_initialization(self, folder):
        repository = legit.Repository(create_folder(folder)).repo
        assert isdir(repository.working_tree_dir)
        assert repository.git_dir.startswith(repository.working_tree_dir)

    def test_initialization_dot_attr(self, folder):
        repository = legit.Repository.init(create_folder(folder)).repo
        assert isdir(repository.working_tree_dir)
        assert repository.git_dir.startswith(repository.working_tree_dir)

    def test_cloning_empty_dir(self, folder):
        if isdir(folder):
            self.change_mod_recursively(folder)
            rmtree(folder)
        cloned_repo = legit.Repository.clone(url, create_folder(folder)).repo
        assert cloned_repo.__class__ is Repo                                    # clone an existing repository
        assert Repo.init(folder).__class__ is Repo
        assert isdir(cloned_repo.working_tree_dir)                              # directory with your work files
        assert cloned_repo.git_dir.startswith(cloned_repo.working_tree_dir)     # directory containing the git repository

    def test_cloning_non_empty_dir(self, folder):
        if isdir(folder):
            self.change_mod_recursively(folder)
            rmtree(folder)
        legit.Repository.init(create_folder(folder))
        cloned_repo = legit.Repository.clone(url, create_folder(folder))
        assert cloned_repo is None                                              # no working tree

    def test_branching(self, folder):
        if isdir(folder):
            self.change_mod_recursively(folder)
            rmtree(folder)
        cloned_repo = legit.Repository.clone(url, create_folder(folder)).repo
        new_branch = cloned_repo.head.reset('feature')                          # create a new branch
        assert cloned_repo.active_branch != new_branch                          # which wasn't checked out yet

    def test_commitnig(self, folder):
        if isdir(folder):
            self.change_mod_recursively(folder)
            rmtree(folder)
        cloned_repo = legit.Repository.clone(url, create_folder(folder)).repo
        new_branch = cloned_repo.create_head('another-branch')
        assert cloned_repo.active_branch != new_branch
        self.assertEqual(new_branch.commit, cloned_repo.active_branch.commit)           # pointing to the checked-out commit
        assert new_branch.set_commit('HEAD~1').commit == cloned_repo.active_branch.commit.parents[0]  #TODO I have a lot of questions about this
