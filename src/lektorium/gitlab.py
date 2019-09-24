import os
import requests


class GitLab:
    def __init__(self, gitlab_url):
        self.gitlab_url = gitlab_url
        self.auth_token = os.environ['GITLAB_TOKEN']
        self.headers = {'Private-Token': self.auth_token}

    def create_merge_request(
        self,
        project_url: str,
        source_branch: str,
        target_branch: str,
        title: str,
        assignee: str
    ) -> bool:
        project_path = self.get_project_path(project_url)
        request_url = f'{self.gitlab_url}/api/v4/projects/{project_path}/merge_requests'
        assignee_id = self.get_user_id(assignee)
        request_data = {'title': title,
                        'source_branch': source_branch,
                        'target_branch': target_branch,
                        'assignee_id': assignee_id}
        response = requests.post(request_url, headers=self.headers, data=request_data)
        if response.status_code == 201:
            return True

    def get_project_path(self, project_url: str) -> str:
        gitlab_url = self.gitlab_url + '/'
        project_path = project_url.replace(gitlab_url, '')
        return project_path.replace('/', '%2f')

    def get_user_id(self, username: str) -> str:
        request_url = f'{self.gitlab_url}/api/v4/users?username={username}'
        response = requests.get(request_url, headers=self.headers).json()
        if response:
            return response[0]['id']
