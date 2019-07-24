import legit
from os.path import expanduser, isdir, exists, join
from os import makedirs, chmod, walk
from shutil import rmtree

url = 'https://github.com/katridi/test_folder'
folder = join(expanduser('~'), 'Desktop\\folder2')


def create_folder(folder: str) -> str:
    if not exists(folder):
        makedirs(folder)
    return folder


def change_mod_recursively(fodler: str, permissions: oct = 0o777) -> None:
    for root, dirs, files in walk(folder):
        for d in dirs:
            chmod(join(root, d), permissions)
        for f in files:
            chmod(join(root, f), permissions)


def test_initialization():
    repository = legit.Repository(create_folder(folder)).repo
    assert isdir(repository.working_tree_dir)
    assert repository.git_dir.startswith(repository.working_tree_dir)


def test_initialization_dot_attr():
    repository = legit.Repository.init(create_folder(folder)).repo
    assert isdir(repository.working_tree_dir)
    assert repository.git_dir.startswith(repository.working_tree_dir)


def test_cloning_empty_dir():
    if isdir(folder):
        change_mod_recursively(folder)
        rmtree(folder)
    repository = legit.Repository.clone(url, create_folder(folder)).repo
    assert isdir(repository.working_tree_dir)
    assert repository.git_dir.startswith(repository.working_tree_dir)


def test_cloning_non_empty_dir():
    if isdir(folder):
        change_mod_recursively(folder)
        rmtree(folder)
    legit.Repository.init(create_folder(folder))
    repository = legit.Repository.clone(url, create_folder(folder))
    assert repository is None


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
