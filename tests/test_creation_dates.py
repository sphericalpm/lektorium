import os
import subprocess
import sys
from pathlib import Path

import yaml


def test_backfill_creation_dates(tmp_path, monkeypatch):
    for role in ('AUTHOR', 'COMMITTER'):
        monkeypatch.setenv('GIT_{}_NAME'.format(role), 'Lektorium Tests')
        monkeypatch.setenv('GIT_{}_EMAIL'.format(role), 'tests@example.com')

    def git(*arguments, env=None):
        return subprocess.check_output(['git', *map(str, arguments)], env=env, text=True).strip()

    site_repository = tmp_path / 'site.git'
    site_workdir = tmp_path / 'site-workdir'
    git('init', '--bare', '--initial-branch=main', site_repository)
    git('clone', site_repository, site_workdir)
    git(
        '-C',
        site_workdir,
        'commit',
        '--allow-empty',
        '-m',
        'Default root',
        env={
            **os.environ,
            'GIT_AUTHOR_DATE': '1500000000 +0000',
            'GIT_COMMITTER_DATE': '1800000000 +0000',
        },
    )
    git('-C', site_workdir, 'push', 'origin', 'main')
    site_head = git('-C', site_repository, 'rev-parse', 'HEAD')

    config_repository = tmp_path / 'config.git'
    config_workdir = tmp_path / 'config-workdir'
    git('init', '--bare', '--initial-branch=main', config_repository)
    git('clone', config_repository, config_workdir)
    config = {
        'default': {'repo': str(site_repository), 'name': 'Default Site'},
        'existing': {'repo': 'unused', 'created': 42},
        'null': {'repo': 'unused', 'created': None},
        'broken': {'repo': str(tmp_path / 'missing.git')},
    }
    (config_workdir / 'config.yml').write_text(yaml.safe_dump(config), encoding='utf-8')
    git('-C', config_workdir, 'add', 'config.yml')
    git('-C', config_workdir, 'commit', '-m', 'Initial config')
    git('-C', config_workdir, 'push', 'origin', 'main')

    monkeypatch.setenv('CI_LEKTORIUM_CONFIG_REPO', str(config_repository))
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'ci' / 'set_creation_dates.py')]
    first = subprocess.run(command, check=True, capture_output=True, text=True)

    updated = yaml.safe_load(git('-C', config_repository, 'show', 'HEAD:config.yml'))
    assert updated == {
        **config,
        'default': {**config['default'], 'created': 1500000000},
    }
    assert git('-C', config_repository, 'rev-list', '--count', 'HEAD') == '2'
    assert git('-C', config_repository, 'log', '-1', '--format=%s') == 'Set site creation dates'
    assert git('-C', config_repository, 'diff', 'HEAD^', 'HEAD', '--name-only') == 'config.yml'
    assert git('-C', site_repository, 'rev-parse', 'HEAD') == site_head
    assert "WARNING: Skipping 'broken'" in first.stdout

    config_head = git('-C', config_repository, 'rev-parse', 'HEAD')
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    assert git('-C', config_repository, 'rev-parse', 'HEAD') == config_head
    assert 'No creation dates changed; no commit needed.' in second.stdout
