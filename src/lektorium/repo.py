import abc
import io
import pathlib
import subprocess
import tempfile
import threading
import dateutil.parser
import yaml


SITES = [{
    'site_id': 'bow',
    'site_name': 'Buy Our Widgets',
    'production_url': 'https://bow.acme.com',
    'staging_url': 'https://bow-test.acme.com',
    'custodian': 'Max Jekov',
    'custodian_email': 'mj@acme.com',
    'sessions': [{
        'session_id': 'widgets-1',
        'edit_url': 'https://cmsdciks.cms.acme.com',
        'view_url': 'https://cmsdciks.build.acme.com',
        'creation_time': dateutil.parser.parse('2019-07-19 10:18 UTC'),
        'custodian': 'Max Jekov',
        'custodian_email': 'mj@acme.com',
    }],
}, {
    'site_id': 'uci',
    'site_name': 'Underpants Collectors International',
    'production_url': 'https://uci.com',
    'staging_url': 'https://uci-staging.acme.com',
    'custodian': 'Mikhail Vartanyan',
    'custodian_email': 'mv@acme.com',
    'sessions': [{
        'session_id': 'pantssss',
        'view_url': 'https://smthng.uci.com',
        'creation_time': dateutil.parser.parse('2019-07-18 11:33 UTC'),
        'custodian': 'Brian',
        'custodian_email': 'brian@splitter.il',
        'parked_time': dateutil.parser.parse('2019-07-18 11:53 UTC'),
    },{
        'session_id': 'pantss1',
        'view_url': 'https://smthng-mu.uci.com',
        'creation_time': dateutil.parser.parse('2019-07-18 11:34 UTC'),
        'custodian': 'Muen',
        'custodian_email': 'muen@flicker.tr',
        'parked_time': dateutil.parser.parse('2019-07-18 11:54 UTC'),
    }],
}, {
    'site_id': 'ldi',
    'site_name': 'Liver Donors Inc.',
    'production_url': 'https://liver.do',
    'staging_url': 'https://pancreas.acme.com',
    'custodian': 'Brian',
    'custodian_email': 'brian@splitter.il'
}]


class Repo:
    @property
    @abc.abstractmethod
    def sites(self):
        pass


class ListRepo(Repo):
    def __init__(self, data):
        self.data = data

    @property
    def sites(self):
        yield from self.data


class GitRepo(Repo):
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
