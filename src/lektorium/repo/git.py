import io
import pathlib
import subprocess
import tempfile
import threading
import yaml
from .interface import Repo as BaseRepo


class Repo(BaseRepo):
    LOCK = threading.Lock()

    def __init__(self, repo):
        self.repo = repo
        self.workdir = tempfile.TemporaryDirectory()

    @property
    def sites(self):
        path = pathlib.Path(self.workdir.name) / 'service'
        with self.LOCK:
            cmd = (
                f'git -C {path} pull'
                if path.exists() else
                f'git clone {self.repo} {path}'
            )
            subprocess.call(cmd, shell=True)
        config = yaml.load(io.BytesIO((path / 'config.yml').read_bytes()))
        for k, v in config.items():
            yield dict(
                site_id=k,
                site_name=v['name'],
                production_url=v['production'],
                staging_url=v['staging'],
                custodian=v['owner'],
                custodian_email=v['email'],
            )
