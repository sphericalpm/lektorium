import abc
import random
import string
from typing import (
    Generator,
    Iterable,
    Mapping,
    Optional,
    Tuple,
)


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

    def generate_session_id(self) -> str:
        session_id = None
        while not session_id or session_id in self.session_ids:
            session_id = ''.join(random.sample(string.ascii_lowercase, 8))
        return session_id

    @property
    @abc.abstractmethod
    def sites(self) -> Iterable:
        pass

    @property
    @abc.abstractmethod
    def sessions(self) -> Mapping:
        pass

    @property
    @abc.abstractmethod
    def session_ids(self) -> Iterable:
        pass

    @property
    @abc.abstractmethod
    def parked_sessions(self) -> Generator:
        pass

    @abc.abstractmethod
    async def create_session(
        self,
        site_id: str,
        custodian: Optional[Tuple[str, str]] = None,
    ) -> str:
        pass

    @abc.abstractmethod
    async def destroy_session(self, session_id: str) -> None:
        pass

    @abc.abstractmethod
    async def park_session(self, session_id: str) -> None:
        pass

    @abc.abstractmethod
    async def unpark_session(self, session_id: str) -> None:
        pass
