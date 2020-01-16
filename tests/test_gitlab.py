import pytest
from os import environ
from unittest import mock
from urllib import parse as url_parse

import respx

from lektorium.repo.local.storage import GitLab
from lektorium.repo.local.templates import (
    AWS_SHARED_CREDENTIALS_FILE_TEMPLATE,
    EMPTY_COMMIT_PAYLOAD,
)


def mock_namespaces(gitlab_instance):
    namespace_id = '2'
    respx.get(
        f'{gitlab_instance.repo_url}/namespaces?search={gitlab_instance.options["namespace"]}',
        headers=gitlab_instance.headers,
        content=[
            {'path': 'fizzle', 'id': '1'},
            {'path': gitlab_instance.options["namespace"], 'id': namespace_id},
            {'path': 'fizzy', 'id': '3'},
        ],
    )
    return namespace_id


def mock_projects(gitlab_instance):
    namespace = gitlab_instance.options["namespace"]
    respx.get(
        f'{gitlab_instance.repo_url}/projects',
        headers=gitlab_instance.headers,
        content=[
            {'path_with_namespace': f'{namespace}/proj1', 'id': '1'},
            {'path_with_namespace': 'other/proj1', 'id': '2'},
            {'path_with_namespace': f'{namespace}/proj2', 'id': '3'},
        ],
    )


def test_repo_url():
    repo_url = GitLab(dict(scheme='http', host='foo')).repo_url
    assert repo_url == f'http://foo/api/{GitLab.DEFAULT_API_VERSION}'

    repo_url = GitLab(dict(scheme='https', host='bar', api_version='v2')).repo_url
    assert repo_url == f'https://bar/api/v2'


def test_path():
    path = GitLab(dict(namespace='foo', project='bar')).path
    assert path == 'foo/bar'


def test_headers():
    headers = GitLab(dict(token='foo')).headers
    assert headers == {'Authorization': 'Bearer foo'}


@pytest.mark.asyncio
@respx.mock
async def test_project_id():
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
    )
    gitlab = GitLab(options)

    mock_projects(gitlab)

    assert await gitlab.project_id == '1'

    options['project'] = 'proj'
    gitlab = GitLab(options)

    with pytest.raises(ValueError):
        await gitlab.project_id


@pytest.mark.asyncio
@respx.mock
async def test_get_namespace_id():
    gitlab = GitLab(dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
    ))

    namespace_id = mock_namespaces(gitlab)

    assert await gitlab.namespace_id == namespace_id


@pytest.mark.asyncio
@respx.mock
async def test_projects():
    gitlab = GitLab(dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
    ))

    mock_projects(gitlab)

    assert len(await gitlab.projects) == 3


@pytest.mark.asyncio
@respx.mock
async def test_create_new_project():
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj',
        branch='master',
    )
    gitlab = GitLab(options)

    namespace_id = mock_namespaces(gitlab)

    def matcher(request, response):
        if request.method != 'POST':
            return None
        if not str(request.url).startswith(f'{gitlab.repo_url}/projects'):
            return None
        query_dict = dict(url_parse.parse_qsl(request.url.query))

        if not all((
            query_dict['name'] == 'proj',
            query_dict['namespace_id'] == namespace_id,
            query_dict['visibility'] == 'private',
            query_dict['default_branch'] == options['branch'],
        )):
            return None
        return response

    respx.request(matcher, headers=gitlab.headers, content={'id': '50'})
    response = await gitlab._create_new_project()

    assert response.status_code == 200
    assert response.json()['id'] == '50'


@pytest.mark.asyncio
@respx.mock
async def test_create_project_variables():
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
    )
    gitlab = GitLab(options)

    key_id = 'key_id'
    secret_key = 'secret_key'
    environ['AWS_ACCESS_KEY_ID'] = key_id
    environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    project_id = '1'
    value = AWS_SHARED_CREDENTIALS_FILE_TEMPLATE.format(
        aws_key_id=key_id,
        aws_secret_key=secret_key,
    )
    aws_variable_name = gitlab.AWS_CREDENTIALS_VARIABLE_NAME

    mock_projects(gitlab)

    def matcher(request, response):
        if request.method != 'POST':
            return None
        if not str(request.url).startswith(f'{gitlab.repo_url}/projects/{project_id}/variables'):
            return None
        query_dict = dict(url_parse.parse_qsl(request.url.query))

        if not all((
            query_dict['id'] == project_id,
            query_dict['variable_type'] == 'file',
            query_dict['key'] == aws_variable_name,
            query_dict['value'] == value,
        )):
            return None
        return response

    respx.request(matcher, headers=gitlab.headers)

    response = await gitlab._create_aws_project_variable()

    assert response.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_create_initial_commit():
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
    )
    gitlab = GitLab(options)

    headers = gitlab.headers
    headers['Content-Type'] = 'application/json'
    project_id = '1'

    mock_projects(gitlab)

    def matcher(request, response):
        if request.method != 'POST':
            return None
        if not str(request.url).startswith(f'{gitlab.repo_url}/projects/{project_id}/repository/commits'):
            return None
        if EMPTY_COMMIT_PAYLOAD not in request.read().decode():
            return None

        return response

    respx.request(matcher, headers=headers)

    response = await gitlab._create_initial_commit()

    assert response.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_init_project():
    new_proj_url = 'git@foo.bar:fizz/new_proj'

    async def create_project():
        mocked = mock.Mock()
        mocked.json = mock.MagicMock(return_value={'ssh_url_to_repo': new_proj_url})
        return mocked

    async def blank():
        pass

    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
        branch='master',
    )
    gitlab = GitLab(options)

    mock_projects(gitlab)

    with pytest.raises(Exception):
        await gitlab.init_project()

    options['project'] = 'new_proj'
    gitlab = GitLab(options)

    with mock.patch.multiple(
        gitlab,
        _create_new_project=create_project,
        _create_aws_project_variable=blank,
        _create_initial_commit=blank,
    ):
        assert await gitlab.init_project() == new_proj_url


@pytest.mark.asyncio
@respx.mock
async def test_merge_requests():
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
        branch='master',
    )
    gitlab = GitLab(options)

    project_id = '1'

    mock_projects(gitlab)
    respx.get(
        f'{gitlab.repo_url}/projects/{project_id}/merge_requests',
        headers=gitlab.headers,
        content=['a', 'b', 'c']
    )

    response = await gitlab.merge_requests

    assert len(response) == 3


@pytest.mark.asyncio
@respx.mock
async def test_create_merge_request():
    src_branch = 'branch_source_abc'
    tgt_branch = 'branch_target_def'
    title = 'request-title-ghi'

    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
        branch='master',
    )
    gitlab = GitLab(options)

    project_id = '1'

    mock_projects(gitlab)

    def matcher(request, response):
        if request.method != 'POST':
            return None
        if not str(request.url).startswith(f'{gitlab.repo_url}/projects/{project_id}/merge_requests'):
            return None
        body = request.read().decode()
        if not all(item in body for item in (src_branch, tgt_branch, title)):
            return None

        return response

    respx.request(matcher, headers=gitlab.headers)

    await gitlab.create_merge_request(
        source_branch=src_branch,
        target_branch=tgt_branch,
        title=title,
    )
