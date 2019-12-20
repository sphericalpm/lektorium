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


NODE_VERSION = '12.4.0'


def install(keep_build_assets=False):
    path = closer(importlib_resources.path(lektorium.__name__, 'client'))
    if (path / 'build').exists():
        return (path / 'build')
    return deploy(path, keep_build_assets)


def deploy(path, keep_build_assets=False):
    source_files = [s.read_bytes() for s in path.rglob('*') if s.is_file()]
    source_hash = hashlib.md5()
    source_hash.update(b''.join(source_files))
    source_hash.update(NODE_VERSION.encode())
    source_hash = source_hash.hexdigest()
    name = lektorium.__name__
    cache = pathlib.Path(appdirs.user_data_dir(name, name)) / source_hash
    if not (cache / 'build').exists():
        if cache.exists():
            shutil.rmtree(cache)
        logging.warn('Building client could take a while')
        try:
            shutil.copytree(path, cache)
            env_dir = cache / 'env'

            subprocess.check_call(('nodeenv', '-n', NODE_VERSION, env_dir))
            subprocess.check_call(
                '. env/bin/activate && npm install && npm run build',
                cwd=cache,
                shell=True
            )

            if not keep_build_assets:
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
    logging.info(f'Using cached client from: "{cache}"')
    return cache / 'build'


if __name__ == '__main__':
    install(keep_build_assets=True)
