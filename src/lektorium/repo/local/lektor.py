import abc
import os
import subprocess


class Lektor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_site(cls, name, owner, folder):
        raise NotImplementedError()


class FakeLektor(Lektor):
    @classmethod
    def create_site(cls, name, owner, folder):
        folder.mkdir(parents=True)


class LocalLektor(Lektor):
    @classmethod
    def create_site(cls, name, owner, folder):
        proc = subprocess.Popen(
            'lektor quickstart',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        proc.communicate(input=os.linesep.join((
            name,
            owner,
            str(folder),
            'Y',
            'Y',
            '',
        )).encode())
        if proc.wait() != 0:
            raise RuntimeError()
