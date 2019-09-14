import abc


class DuplicateEditSession(Exception):
    pass


class SessionNotFound(Exception):
    pass


class Repo(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def sites(self):
        pass

    @property
    @abc.abstractmethod
    def sessions(self):
        pass
