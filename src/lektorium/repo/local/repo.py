import datetime
import functools
import inifile
import pathlib
import shutil
import tempfile

import yaml
from cached_property import cached_property

from ...utils import closer
from ..interface import (
    DuplicateEditSession,
    InvalidSessionState,
    Repo as BaseRepo,
    SessionNotFound,
)
from .config import Config
from .objects import Session, Site


class Repo(BaseRepo):
    def __init__(self, root_dir, server, lektor):
        self.root_dir = pathlib.Path(root_dir)
        self.server = server
        self.lektor = lektor
        self.init_sites()

    def init_sites(self):
        for site_id, site in self.config.items():
            if site.production_url is None:
                site_root = self.root_dir / site_id / 'master'
                site.production_url = self.server.serve_static(site_root)

    @cached_property
    def session_dir(self):
        return pathlib.Path(closer(tempfile.TemporaryDirectory()))

    @cached_property
    def config(self):
        config_path = (self.root_dir / 'config.yml')
        config = {}
        if config_path.exists():
            with config_path.open('rb') as config_file:
                def iter_sites(config_file):
                    config_data = yaml.load(config_file, Loader=yaml.Loader)
                    for site_id, props in config_data.items():
                        url = props.pop('url', None)
                        if url is None:
                            site_root = self.root_dir / site_id / 'master'
                            config = list(site_root.glob('*.lektorproject'))
                            if config:
                                config = inifile.IniFile(config[0])
                                name = config.get('project.name')
                                if name is not None:
                                    props['name'] = name
                                project_url = config.get('project.url')
                                if project_url is not None:
                                    url = project_url
                        props['production_url'] = url
                        props['site_id'] = site_id
                        yield props
                sites = (Site(**props) for props in iter_sites(config_file))
                config = {s['site_id']: s for s in sites}
        return Config(config_path, config)

    @property
    def sites(self):
        yield from self.config.values()

    @property
    def sessions(self):
        def iterate():
            for site in self.config.values():
                for session_id, session in site.sessions.items():
                    yield session_id, (session, site)
        return dict(iterate())

    @property
    def parked_sessions(self):
        for site in self.config.values():
            for session in site.sessions.values():
                if session.parked:
                    yield session

    def create_session(self, site_id, custodian=None):
        custodian, custodian_email = custodian or self.DEFAULT_USER
        site = self.config[site_id]
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        session_id = self.generate_session_id()
        session_dir = self.session_dir / site_id / session_id
        shutil.copytree(self.root_dir / site_id / 'master', session_dir)
        session_object = Session(
            session_id=session_id,
            creation_time=datetime.datetime.now(),
            view_url=None,
            edit_url=self.server.serve_lektor(session_dir),
            custodian=custodian,
            custodian_email=custodian_email,
        )
        self.config[site_id].sessions[session_id] = session_object
        return session_id

    def destroy_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        site = self.sessions[session_id][1]
        session_dir = self.session_dir / site['site_id'] / session_id
        self.server.stop_server(
            session_dir,
            functools.partial(shutil.rmtree, session_dir)
        )
        site.sessions.pop(session_id)

    def park_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        session_dir = self.session_dir / site['site_id'] / session_id
        if session.parked:
            raise InvalidSessionState()
        self.server.stop_server(session_dir)
        session['edit_url'] = None
        session['parked_time'] = datetime.datetime.now()

    def unpark_session(self, session_id):
        if session_id not in self.sessions:
            raise SessionNotFound()
        session, site = self.sessions[session_id]
        session_dir = (self.session_dir / site['site_id'] / session_id)
        if not session.parked:
            raise InvalidSessionState()
        if any(not s.parked for s in site.sessions.values()):
            raise DuplicateEditSession()
        session['edit_url'] = self.server.serve_lektor(session_dir)
        session.pop('parked_time', None)

    def create_site(self, site_id, name, owner=None):
        owner, email = owner or self.DEFAULT_USER
        master_path = self.root_dir / site_id / 'master'
        self.lektor.create_site(name, owner, master_path)
        self.config[site_id] = Site(site_id, **dict(
            name=name,
            owner=owner,
            email=email,
            production_url=self.server.serve_static(master_path)
        ))
