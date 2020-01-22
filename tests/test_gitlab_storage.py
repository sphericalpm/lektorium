import pytest
import subprocess
from unittest import mock

from lektorium.repo.local.storage import GitlabStorage, GitStorage, GitLab, AWS
from conftest import mock_async_fn


@pytest.mark.asyncio
async def test_gitlabstorage(tmpdir):
    remote_dir = tmpdir / 'remote'
    local_dir = tmpdir / 'local'
    remote_dir.mkdir()
    local_dir.mkdir()
    subprocess.check_call('git init --bare .', shell=True, cwd=remote_dir)
    subprocess.check_call(f'git clone {remote_dir} .', shell=True, cwd=local_dir)

    with mock.patch.multiple(
        AWS,
        create_s3_bucket=mock_async_fn('bucket_name'),
        create_cloudfront_distribution=mock_async_fn(('dist_id', 'domain_name')),
        open_bucket_access=mock_async_fn(None),
    ):
        with mock.patch.multiple(
            GitLab,
            init_project=mock_async_fn('site_repo'),
        ):
            with mock.patch.multiple(
                GitStorage,
                __init__=lambda *args, **kwargs: None,
                create_site=mock_async_fn((local_dir, {})),
            ):
                storage = GitlabStorage(
                    'git@server.domain:namespace/reponame.git',
                    'token',
                    'protocol',
                )

                assert storage.repo == 'server.domain'
                assert storage.namespace == 'namespace'

                site_workdir, options = await storage.create_site(None, 'foo', '', 'bar')

                assert (local_dir / '.gitlab-ci.yml').exists()
                assert (local_dir / 'foo.lektorproject').exists()
                assert site_workdir == local_dir
                assert options == {
                    'cloudfront_domain_name': 'domain_name',
                    'production_url': 'https://domain_name',
                    'gitlab': {
                        'scheme': 'protocol',
                        'host': 'server.domain',
                        'namespace': 'namespace',
                        'project': 'bar',
                        'token': 'token'
                    }
                }

                assert await storage.create_site_repo('') == 'site_repo'
