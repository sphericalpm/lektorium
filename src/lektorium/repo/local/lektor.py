import abc
import os
import asyncio


class Lektor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def quickstart(cls, name, owner, folder):
        raise NotImplementedError()


class FakeLektor(Lektor):
    @classmethod
    async def quickstart(cls, name, owner, folder):
        folder.mkdir(parents=True)
        (folder / 'fake-lektor.file').touch()


class LocalLektor(Lektor):
    @classmethod
    async def quickstart(cls, name, owner, folder):
        proc = await asyncio.create_subprocess_shell(
            'lektor quickstart',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate(input=os.linesep.join((
            name,
            owner,
            str(folder),
            'n',
            'Y',
            '',
        )).encode())
        if await proc.wait() != 0:
            raise RuntimeError()
