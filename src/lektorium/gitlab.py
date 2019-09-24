import os
import requests


class GitLab:
    def __init__(self, gitlab_url):
        self.gitlab_url = gitlab_url
        self.auth_token = os.environ['GITLAB_TOKEN']
        self.headers = {'Private-Token': self.auth_token}

    def create_merge_request(
        self,
        project_url,
        source_branch,
        target_branch,
        title,
        assignee
    ):
        pass

    def get_project_path(self, project_url):
        gitlab_url = self.gitlab_url + '/'
        return project_url.replace(gitlab_url, '')

    def get_user_id(self, username):
        request_url = f"{self.gitlab_url}/api/v4/users?username={username}"
        response = requests.get(request_url, headers=self.headers).json()
        if response:
            return response[0]['id']
