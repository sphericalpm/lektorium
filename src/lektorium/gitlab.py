import os
import requests


class GitLab:
    def __init__(self, gitlab_url):
        self.gitlab_url = gitlab_url
        self.auth_token = os.environ['GITLAB_TOKEN']

    def create_merge_request(
        self,
        project_url,
        source_branch,
        target_branch,
        title,
        assignee
    ):
        pass