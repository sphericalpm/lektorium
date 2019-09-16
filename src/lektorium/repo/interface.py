import abc
import random
import string


class ExceptionBase(Exception):
    pass


class DuplicateEditSession(ExceptionBase):
    pass


class InvalidSessionState(ExceptionBase):
    pass


class SessionNotFound(ExceptionBase):
    pass


class Repo(metaclass=abc.ABCMeta):
    DEFAULT_USER = ('User Interface Py', 'user@interface.py')

    def generate_session_id(self):
        session_id = None
        while not session_id or session_id in self.sessions:
            session_id = ''.join(random.sample(string.ascii_lowercase, 8))
        return session_id

    @property
    @abc.abstractmethod
    def sites(self):
        pass

    @property
    @abc.abstractmethod
    def sessions(self):
        pass

    @property
    @abc.abstractmethod
    def parked_sessions(self):
        pass

    @abc.abstractmethod
    def create_session(self, site_id, custodian=None):
        pass

    @abc.abstractmethod
    def destroy_session(self, session_id):
        pass

    @abc.abstractmethod
    def park_session(self, session_id):
        pass

    @abc.abstractmethod
    def unpark_session(self, session_id):
        pass
