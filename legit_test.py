import legit
from os.path import expanduser, isdir, exists, join
from os import makedirs

folder = join(expanduser('~'), '/Desktop/folder2')
if not exists(folder):
    makedirs(folder)


def test_initialization():
    repository = legit.Repository(folder).repo
    assert isdir(repository.working_tree_dir)
    assert repository.git_dir.startswith(repository.working_tree_dir)


def test_initialization_dot_attr():
    repository = legit.Repository(folder).repo
    assert isdir(repository.working_tree_dir)
    assert repository.git_dir.startswith(repository.working_tree_dir)


def test_cloning():
    pass


def test_branching():
    pass


def test_adding_files():
    pass


def test_commitnig():
    pass


def test_merging():
    pass


def test_pushing():
    pass
