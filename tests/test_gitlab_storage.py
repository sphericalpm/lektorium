import subprocess
from unittest import mock

import pytest

from lektorium.repo.local.storage import AWS, GitLab, GitlabStorage, GitStorage


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
        create_s3_bucket=lambda *args, **kwargs: 'bucket_name',
        create_cloudfront_distribution=lambda *args, **kwargs: ('dist_id', 'domain_name'),
        open_bucket_access=lambda *args, **kwargs: None,
    ):
        with mock.patch.multiple(
            GitLab,
            init_project=lambda *args, **kwargs: 'site_repo',
        ):
            async def mock_create_site(*args, **kwargs):
                return local_dir, {}
            with mock.patch.multiple(
                GitStorage,
                __init__=lambda *args, **kwargs: None,
                create_site=mock_create_site
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
                    'url': 'https://domain_name',
                }

                assert await storage.create_site_repo('') == 'site_repo'
