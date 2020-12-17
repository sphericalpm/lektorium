import base64
import io
import os

import pytest
import requests
import yaml

from lektorium.repo.local.storage import GitLab, GitStorage


@pytest.mark.skipif(
    'LEKTORIUM_GITLAB_TEST' not in os.environ,
    reason='no LEKTORIUM_GITLAB_TEST in env',
)
def test_gitlab_real():
    gitlab = os.environ['LEKTORIUM_GITLAB_TEST']
    options = gitlab.split(':')
    options = dict(x.split('=') for x in options)
    gitlab = GitLab(options)
    response = requests.get(
        (
            '{scheme}://{host}/api/{api_version}/projects'
            '/{config}/repository/files/{filename}'
        ).format(
            filename=GitStorage.CONFIG_FILENAME,
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
        gitlab = GitLab(options)
        assert isinstance(gitlab.project_id, int)
