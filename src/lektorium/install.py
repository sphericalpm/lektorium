import hashlib
try:
    import importlib.resources as importlib_resources
except ModuleNotFoundError:
    import importlib_resources
import logging
import pathlib
import shutil
import subprocess
import appdirs
import lektorium
from .utils import closer


def install():
    path = closer(importlib_resources.path(lektorium.__name__, 'client'))
    if (path / 'build').exists():
        return (path / 'build')
    return deploy(path)


def deploy(path):
    source_files = [s.read_bytes() for s in path.rglob('*') if s.is_file()]
    source_hash = hashlib.md5()
    source_hash.update(b''.join(source_files))
    source_hash = source_hash.hexdigest()
    name = lektorium.__name__
    cache = pathlib.Path(appdirs.user_data_dir(name, name)) / source_hash
    if (cache / 'build').exists():
        return cache / 'build'
    elif cache.exists():
        shutil.rmtree(cache)
    logging.warn('Building client could tak a while')
    try:
        shutil.copytree(path, cache)
        env_dir = cache / 'env'

        subprocess.check_call(('nodeenv', '-n', '10.16.3', env_dir))
        subprocess.check_call(
            '. env/bin/activate && npm install && npm run build',
            cwd=cache,
            shell=True
        )

        for entry in cache.iterdir():
            if entry.name == 'build':
                continue
            elif entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    except Exception:
        if cache.exists():
            shutil.rmtree(cache)
        raise
    return cache / 'build'


if __name__ == '__main__':
    install()
