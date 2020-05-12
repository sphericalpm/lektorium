from os import environ
from unittest import mock

import pytest

from lektorium.repo.local.storage import GitLab
from lektorium.repo.local.templates import (
    AWS_SHARED_CREDENTIALS_FILE_TEMPLATE,
    EMPTY_COMMIT_PAYLOAD,
)


def mock_namespaces(mocker, gitlab_instance):
    namespace_id = '2'
    mocker.get(
        f'{gitlab_instance.repo_url}/groups',
        request_headers=gitlab_instance.headers,
        json=[],
    )
    mocker.get(
        f'{gitlab_instance.repo_url}/namespaces',
        request_headers=gitlab_instance.headers,
        json=[
            {'path': 'fizzle', 'id': '1'},
            {'path': gitlab_instance.options["namespace"], 'id': namespace_id},
            {'path': 'fizzy', 'id': '3'},
        ],
    )
    return namespace_id


def mock_projects(mocker, gitlab_instance):
    namespace = gitlab_instance.options["namespace"]
    mocker.get(
        f'{gitlab_instance.repo_url}/projects',
        request_headers=gitlab_instance.headers,
        json=[
            {'path_with_namespace': f'{namespace}/proj1', 'id': '1'},
            {'path_with_namespace': 'other/proj1', 'id': '2'},
            {'path_with_namespace': f'{namespace}/proj2', 'id': '3'},
        ],
    )


def test_repo_url():
    repo_url = GitLab(dict(scheme='http', host='foo')).repo_url
    assert repo_url == f'http://foo/api/{GitLab.DEFAULT_API_VERSION}'

    repo_url = GitLab(dict(scheme='https', host='bar', api_version='v2')).repo_url
    assert repo_url == 'https://bar/api/v2'


def test_path():
    path = GitLab(dict(namespace='foo', project='bar')).path
    assert path == 'foo/bar'


def test_headers():
    headers = GitLab(dict(token='foo')).headers
    assert headers == {'Authorization': 'Bearer foo'}


def test_project_id(requests_mock):
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
    )
    gitlab = GitLab(options)

    mock_projects(requests_mock, gitlab)

    assert gitlab.project_id == '1'

    options['project'] = 'proj'
    gitlab = GitLab(options)

    with pytest.raises(ValueError):
        gitlab.project_id


def test_get_namespace_id(requests_mock):
    gitlab = GitLab(dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
    ))

    namespace_id = mock_namespaces(requests_mock, gitlab)

    assert gitlab.namespace_id == namespace_id


def test_projects(requests_mock):
    gitlab = GitLab(dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
    ))

    mock_projects(requests_mock, gitlab)

    assert len(gitlab.projects) == 3


def test_create_new_project(requests_mock):
    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj',
        branch='master',
    )
    gitlab = GitLab(options)

    namespace_id = mock_namespaces(requests_mock, gitlab)

    requests_mock.post(
        (
            f'{gitlab.repo_url}/projects?name=proj&namespace_id={namespace_id}'
            f'&visibility=private&default_branch={options["branch"]}'
        ),
        request_headers=gitlab.headers,
        json={'id': '50'},
    )

    response = gitlab._create_new_project()

    assert response.status_code == 200
    assert response.json()['id'] == '50'


def test_create_project_variables(requests_mock):
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

    mock_projects(requests_mock, gitlab)
    requests_mock.post(
        (
            f'{gitlab.repo_url}/projects/{project_id}/variables?id={project_id}'
            f'&variable_type=file&key={aws_variable_name}&value={value}'
        ),
        request_headers=gitlab.headers,
    )

    response = gitlab._create_aws_project_variable()

    assert response.status_code == 200


def test_create_initial_commit(requests_mock):
    def additional_matcher(request):
        return EMPTY_COMMIT_PAYLOAD in request.text

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

    mock_projects(requests_mock, gitlab)
    requests_mock.post(
        f'{gitlab.repo_url}/projects/{project_id}/repository/commits',
        request_headers=headers,
        additional_matcher=additional_matcher,
    )

    response = gitlab._create_initial_commit()

    assert response.status_code == 200


def test_init_project(requests_mock):
    new_proj_url = 'git@foo.bar:fizz/new_proj'

    def create_project():
        mocked = mock.Mock()
        mocked.json = mock.MagicMock(return_value={'ssh_url_to_repo': new_proj_url})
        return mocked

    options = dict(
        scheme='http',
        host='foo.bar',
        token='buzz',
        namespace='fizz',
        project='proj1',
        branch='master',
    )
    gitlab = GitLab(options)

    mock_projects(requests_mock, gitlab)

    with pytest.raises(Exception):
        gitlab.init_project()

    options['project'] = 'new_proj'
    gitlab = GitLab(options)

    with mock.patch.multiple(
        gitlab,
        _create_new_project=create_project,
        _create_aws_project_variable=lambda: None,
        _create_initial_commit=lambda: None,
    ):
        pp = gitlab.init_project()

        assert pp == new_proj_url


def test_merge_requests(requests_mock):
    src_branch = 'branch_source_abc'
    tgt_branch = 'branch_target_def'
    title = 'request title ghi'

    def additional_matcher(request):
        return all(
            item in request.text for item in (src_branch, tgt_branch, title)
        )

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

    mock_projects(requests_mock, gitlab)
    requests_mock.get(
        f'{gitlab.repo_url}/projects/{project_id}/merge_requests',
        request_headers=gitlab.headers,
        json=['a', 'b', 'c']
    )

    response = gitlab.merge_requests

    assert len(response) == 3


def test_create_merge_request(requests_mock):
    src_branch = 'branch_source_abc'
    tgt_branch = 'branch_target_def'
    title = 'request-title-ghi'

    def additional_matcher(request):
        return all(
            item in request.text for item in (src_branch, tgt_branch, title)
        )

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

    mock_projects(requests_mock, gitlab)
    requests_mock.post(
        f'{gitlab.repo_url}/projects/{project_id}/merge_requests',
        request_headers=gitlab.headers,
        additional_matcher=additional_matcher,
    )

    gitlab.create_merge_request(
        source_branch=src_branch,
        target_branch=tgt_branch,
        title=title,
    )
