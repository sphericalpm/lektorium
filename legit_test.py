import legit
from os.path import expanduser, isdir, exists, join
from os import makedirs, chmod
from shutil import rmtree

url = 'https://github.com/katridi/test_folder'
folder = join(expanduser('~'), 'Desktop\\folder2')


def create_folder(folder: str) -> str:
    if not exists(folder):
        makedirs(folder)
    return folder


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
        chmod(folder, 0o777)
        rmtree(folder)
    repository = legit.Repository.clone(url, create_folder(folder)).repo
    assert isdir(repository.working_tree_dir)
    assert repository.git_dir.startswith(repository.working_tree_dir)


# def test_cloning_non_empty_dir():
#     legit.Repository.init(create_folder(folder))
#     repository = legit.Repository.clone(url, create_folder(folder))
#     assert repository is None


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
