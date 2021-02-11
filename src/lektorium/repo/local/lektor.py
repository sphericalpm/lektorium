import abc
import os
import subprocess


class Lektor(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def quickstart(cls, name, owner, folder):
        raise NotImplementedError()


class FakeLektor(Lektor):
    @classmethod
    def quickstart(cls, name, owner, folder):
        folder.mkdir(parents=True)
        (folder / 'fake-lektor.file').touch()


class LocalLektor(Lektor):
    @classmethod
    def quickstart(cls, name, owner, folder):
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
            'n',
            'Y',
            '',
        )).encode())
        if proc.wait() != 0:
            raise RuntimeError()
