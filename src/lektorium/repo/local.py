from .interface import Repo as BaseRepo


class Repo(BaseRepo):
    def __init__(self, repo_root_dir):
        self.repo_root_dir = repo_root_dir

    @property
    def sites(self):
        raise NotImplementedError()

    @property
    def sessions(self):
        raise NotImplementedError()

    @property
    def parked_sessions(self):
        raise NotImplementedError()

    def create_session(self, site_id):
        raise NotImplementedError()

    def destroy_session(self, session_id):
        raise NotImplementedError()

    def park_session(self, session_id):
        raise NotImplementedError()

    def unpark_session(self, session_id):
        raise NotImplementedError()
