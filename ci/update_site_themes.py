#!/usr/bin/env python3
"""Update site theme submodules in repositories listed by Lektorium config."""

import os
import re
import subprocess
import tempfile
from pathlib import Path

import yaml


COMMIT_MESSAGE = 'Update site themes and trigger rebuild'


def run(command, capture_output=False, check=True):
    """Run a command and optionally return its standard output."""
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        universal_newlines=True,
    )
    if check and result.returncode:
        message = result.stderr.strip() if capture_output else ''
        raise RuntimeError(
            'Command failed with exit code {}: {}{}'.format(
                result.returncode,
                ' '.join(command),
                '\n{}'.format(message) if message else '',
            )
        )
    return result


def repositories_from_config(config_path):
    """Return (alias, repository URL) pairs from config.yml."""
    with config_path.open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file) or {}

    if not isinstance(config, dict):
        raise ValueError('{} must contain a YAML mapping'.format(config_path))

    repositories = []
    for alias, settings in config.items():
        if not isinstance(settings, dict) or 'repo' not in settings:
            print(
                '\033[1;33m!!! WARNING: {!r} has no repo configured; skipping !!!\033[0m'.format(
                    alias,
                ),
                flush=True,
            )
            continue
        repository = settings['repo']
        if not isinstance(repository, str) or not repository.strip():
            print(
                '\033[1;33m!!! WARNING: {!r} has an invalid repo value; skipping !!!\033[0m'.format(
                    alias,
                ),
                flush=True,
            )
            continue
        repositories.append((str(alias), repository.strip()))

    if not repositories:
        raise ValueError('No repository entries were found in {}'.format(config_path))
    return repositories


def repositories_from_override(value):
    """Parse repository URLs separated by whitespace or commas."""
    repository_urls = [item for item in re.split(r'[\s,]+', value.strip()) if item]
    return [('override-{}'.format(index), repository) for index, repository in enumerate(repository_urls, start=1)]


def update_repository(alias, repository_url, checkout_path):
    """Update theme submodules and push a rebuild commit to a site repository."""
    print('Updating {} ({})'.format(alias, repository_url), flush=True)
    run(['git', 'clone', '--recurse-submodules', repository_url, str(checkout_path)])

    run(['git', '-C', str(checkout_path), 'submodule', 'sync', '--recursive'])
    run(['git', '-C', str(checkout_path), 'submodule', 'update', '--init', '--remote', '--recursive'])
    run(['git', '-C', str(checkout_path), 'diff', '--check'])
    run(['git', '-C', str(checkout_path), 'add', '--all'])

    changes = run(['git', '-C', str(checkout_path), 'diff', '--cached', '--quiet'], check=False)
    if changes.returncode == 0:
        print('{} submodules are already current; creating an empty commit'.format(alias), flush=True)
    elif changes.returncode != 1:
        raise RuntimeError('Could not inspect staged changes for {}'.format(alias))

    run(['git', '-C', str(checkout_path), 'commit', '--allow-empty', '-m', COMMIT_MESSAGE])
    run(['git', '-C', str(checkout_path), 'push'])


def main():
    """Load the site repository list and update each repository's submodules."""
    repository_override = os.environ.get('CI_SITE_UPDATE_REPOS', '').strip()

    with tempfile.TemporaryDirectory(prefix='lektorium-site-themes-update-') as temp_directory:
        temp_path = Path(temp_directory)
        if repository_override:
            print('Using CI_SITE_UPDATE_REPOS instead of config.yml', flush=True)
            repositories = repositories_from_override(repository_override)
        else:
            config_repository = os.environ.get('CI_LEKTORIUM_CONFIG_REPO', '').strip()
            if not config_repository:
                raise ValueError('CI_LEKTORIUM_CONFIG_REPO must be set when CI_SITE_UPDATE_REPOS is empty')
            config_path = temp_path / 'config-repository'
            print('Cloning the Lektorium config repository', flush=True)
            run(['git', 'clone', config_repository, str(config_path)])
            repositories = repositories_from_config(config_path / 'config.yml')

        repositories_path = temp_path / 'repositories'
        repositories_path.mkdir()
        failed_repositories = []
        for index, (alias, repository_url) in enumerate(repositories, start=1):
            try:
                update_repository(
                    alias,
                    repository_url,
                    repositories_path / f'{alias}-{index}',
                )
            except Exception as error:
                print(
                    '\033[1;31m!!! ERROR: Failed to update {!r} ({}): {} !!!\033[0m'.format(
                        alias,
                        repository_url,
                        error,
                    ),
                    flush=True,
                )
                failed_repositories.append((alias, repository_url))

        if failed_repositories:
            divider = '\033[1;33m{}\033[0m'.format('=' * 72)
            print(divider)
            print('\033[1;31mRepositories that failed to update:\033[0m')
            for alias, repository_url in failed_repositories:
                print('  - {!r}: {}'.format(alias, repository_url))
            print(divider)


if __name__ == '__main__':
    main()
