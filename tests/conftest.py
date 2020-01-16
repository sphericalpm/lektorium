import pathlib
import subprocess
import pytest
import wrapt
import asyncio
import respx
from lektorium.repo import LocalRepo
from lektorium.repo.local import (
    FileStorage,
    GitStorage,
    FakeServer,
    FakeLektor,
)
from lektorium.repo.memory import VALID_MERGE_REQUEST


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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(repo.create_site('bow', 'Buy Our Widgets'))
    loop.run_until_complete(repo.create_site('uci', 'Underpants Collectors International'))

    return repo


def git_repo(root_dir):
    repo = local_repo(root_dir, git_prepare(GitStorage))
    repo.config['bow'].data[GitStorage.GITLAB_SECTION_NAME] = {
        'scheme': 'https',
        'host': 'server',
        'token': '123token456',
        'namespace': 'user',
        'project': 'project',
    }
    return repo


@pytest.fixture
def merge_requests():
    with respx.mock():
        project = {
            'id': 122,
            'path_with_namespace': 'user/project',
        }
        merge_requests = [
            VALID_MERGE_REQUEST,
            {
                'id': 124,
                'title': 'test2',
                'target_branch': 'master',
                'source_branch': 'test2',
                'state': '2',
                'web_url': 'url124',
            }
        ]
        respx.get(
            'https://server/api/v4/projects',
            content=[project],
        )
        respx.get(
            f'https://server/api/v4/projects/{project["id"]}/merge_requests',
            content=merge_requests,
        )
        return merge_requests
