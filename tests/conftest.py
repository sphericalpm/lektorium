import pathlib
import subprocess
import pytest
import requests_mock
import wrapt
from lektorium.repo import LocalRepo
from lektorium.repo.local import (
    FileStorage,
    GitStorage,
    FakeServer,
    FakeLektor,
)


@wrapt.decorator
def git_prepare(wrapped, instance, args, kwargs):
    assert not len(kwargs)
    tmpdir, = args
    tmpdir = tmpdir / 'lektorium'
    if not tmpdir.exists():
        tmpdir.mkdir()
    if not (tmpdir / '.git').exists():
        subprocess.check_call('git init --bare .', shell=True, cwd=tmpdir)
    return wrapped(pathlib.Path(tmpdir))


def local_repo(root_dir, storage_factory=FileStorage):
    repo = LocalRepo(storage_factory(root_dir), FakeServer(), FakeLektor)
    repo.create_site('bow', 'Buy Our Widgets')
    repo.create_site('uci', 'Underpants Collectors International')
    return repo


def git_repo(root_dir):
    return local_repo(root_dir, git_prepare(GitStorage))


@pytest.fixture
def merge_requests():
    with requests_mock.Mocker() as m:
        project = {
            'id': 122,
            'path_with_namespace': 'user/project'
        }
        merge_requests = [{
            'id': 123,
            'title': 'Request from "MJ" <mj@spherical.pm>',
            'target_branch': 'master',
            'source_branch': 'test1'
        }, {
            'id': 124,
            'title': 'test2',
            'target_branch': 'master',
            'source_branch': 'test2'
        }]
        m.get(
            'https://server/api/v4/projects',
            json=[
                project
            ]
        )
        m.get(
            f'https://server/api/v4/projects/{project["id"]}/merge_requests',
            json=merge_requests
        )
        yield merge_requests
