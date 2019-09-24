import os
import requests

from typing import Optional


class GitLab:
    def __init__(self, gitlab_url):
        self.gitlab_url = gitlab_url
        self.headers = {'Private-Token': os.environ['GITLAB_TOKEN']}

    def create_merge_request(
        self,
        project_url: str,
        source_branch: str,
        target_branch: str,
        title: str,
        assignee: str
    ) -> Optional[bool]:
        project_path = self.get_project_path(project_url)
        url = f'{self.gitlab_url}/api/v4/projects/{project_path}/merge_requests'
        assignee_id = self.get_user_id(assignee)
        data = {'title': title,
                'source_branch': source_branch,
                'target_branch': target_branch,
                'assignee_id': assignee_id}
        result = requests.post(url, headers=self.headers, data=data)
        if result.status_code == 201:
            return True

    def get_project_path(self, project_url: str) -> str:
        gitlab_url = self.gitlab_url + '/'
        project_path = project_url.replace(gitlab_url, '')
        return project_path.replace('/', '%2f')

    def get_user_id(self, username: str) -> str:
        url = f'{self.gitlab_url}/api/v4/users?username={username}'
        result = requests.get(url, headers=self.headers).json()
        if result:
            return result[0]['id']
