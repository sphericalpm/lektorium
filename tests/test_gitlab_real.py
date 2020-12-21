import base64
import io
import os

import pytest
import requests
import yaml

from lektorium.repo.local import storage


@pytest.mark.skipif(
    'LEKTORIUM_GITLAB_TEST' not in os.environ,
    reason='no LEKTORIUM_GITLAB_TEST in env',
)
def test_gitlab_real():
    gitlab = os.environ['LEKTORIUM_GITLAB_TEST']
    options = gitlab.split(':')
    options = dict(x.split('=') for x in options)
    gitlab = storage.GitLab(options)
    response = requests.get(
        (
            '{scheme}://{host}/api/{api_version}/projects'
            '/{config}/repository/files/{filename}'
        ).format(
            filename=storage.GitStorage.CONFIG_FILENAME,
            **gitlab.options,
        ),
        headers=gitlab.headers,
        params=dict(ref='master'),
    )
    response.raise_for_status()
    config = response.json()['content']
    config = base64.b64decode(config)
    config = yaml.load(io.BytesIO(config))
    response = requests.get(
        (
            '{scheme}://{host}/api/{api_version}/projects'
            '/{config}'
        ).format(**gitlab.options),
        headers=gitlab.headers,
    )
    response.raise_for_status()
    options['namespace'] = response.json()['namespace']['full_path']
    for name in config.keys():
        options['project'] = name
        gitlab = storage.GitLab(options)
        assert isinstance(gitlab.project_id, int)


@pytest.mark.skipif(
    'LEKTORIUM_GITLAB_TEST' not in os.environ,
    reason='no LEKTORIUM_GITLAB_TEST in env',
)
def test_gitlab_merge_requests():
    gitlab = os.environ['LEKTORIUM_GITLAB_TEST']
    options = gitlab.split(':')
    options = dict(x.split('=') for x in options)
    options['protocol'] = options.pop('scheme')
    host = options.pop('host')
    config = options.pop('config')
    storage.run = lambda *args, **kwargs: None
    gitlab = storage.GitlabStorage(
        git=f'git@{host}:{config}/{storage.GitStorage.CONFIG_FILENAME}',
        **options,
    )
    gitlab.get_merge_requests('000')
    gitlab.get_merge_requests('1111')
