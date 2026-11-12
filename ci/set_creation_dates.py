#!/usr/bin/env python3
"""Backfill missing site creation dates from repository root commits."""

import os
import subprocess
import tempfile
from pathlib import Path

import yaml


COMMIT_MESSAGE = 'Set site creation dates'


def run(command, capture_output=False):
    """Run a command, optionally capturing its standard output."""
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE if capture_output else None,
        universal_newlines=True,
    )


def repository_creation_time(settings):
    """Read the oldest root-commit author timestamp without checking out files."""
    repository = settings['repo'].strip()

    with tempfile.TemporaryDirectory(prefix='lektorium-site-history-') as directory:
        checkout = str(Path(directory) / 'repo.git')
        command = ['git', 'clone', '--bare', '--filter=tree:0', '--single-branch', '--no-tags']
        run([*command, '--', repository, checkout])
        result = run(['git', '-C', checkout, 'log', '--max-parents=0', '--format=%at'], capture_output=True)
        timestamps = [int(value) for value in result.stdout.splitlines()]
        if not timestamps:
            raise ValueError('repository has no root commits')
        return min(timestamps)


def main():
    """Update missing dates and push one commit to the config repository."""
    config_repository = os.environ.get('CI_LEKTORIUM_CONFIG_REPO', '').strip()
    if not config_repository:
        raise ValueError('CI_LEKTORIUM_CONFIG_REPO must be set')

    with tempfile.TemporaryDirectory(prefix='lektorium-creation-dates-') as directory:
        checkout = Path(directory) / 'config-repository'
        run(['git', 'clone', '--', config_repository, str(checkout)])
        config_path = checkout / 'config.yml'
        with config_path.open(encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
        if not isinstance(config, dict):
            raise ValueError('config.yml must contain a YAML mapping')

        updated = 0
        failed = []
        for alias, settings in config.items():
            if isinstance(settings, dict) and 'created' in settings:
                continue
            try:
                if not isinstance(settings, dict):
                    raise ValueError('site settings must contain a YAML mapping')
                settings['created'] = repository_creation_time(settings)
                updated += 1
                print(f'\033[1;32mSet creation date for {alias!r}: {settings["created"]}\033[0m', flush=True)
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                print(f'\033[1;33m!!! WARNING: Skipping {alias!r}: {error} !!!\033[0m', flush=True)
                failed.append(alias)

        if updated:
            with config_path.open('w', encoding='utf-8') as config_file:
                yaml.safe_dump(config, config_file, sort_keys=False, allow_unicode=True)
            run(['git', '-C', str(checkout), 'add', '--', 'config.yml'])
            run(['git', '-C', str(checkout), 'commit', '-m', COMMIT_MESSAGE])
            run(['git', '-C', str(checkout), 'push'])
        else:
            print('\033[1;34mNo creation dates changed; no commit needed.\033[0m', flush=True)

        color = '\033[1;33m' if failed else '\033[1;32m'
        print(f'{color}Set creation dates for {updated} site(s); skipped {len(failed)} failed site(s).\033[0m', flush=True)
        if failed:
            divider = f'\033[1;33m{"=" * 72}\033[0m'
            print(divider)
            print('\033[1;31mSites without a new creation date:\033[0m')
            for alias in failed:
                print(f'  - {alias!r}')
            print(divider)


if __name__ == '__main__':
    main()
