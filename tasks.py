import os
from invoke import task
from invoke.tasks import call


CONTAINERS_BASE = 'containers'
IMAGE = 'lektorium'
CONTAINER = IMAGE
LEKTOR_BASE = PROXY_BASE = 'alpine:v3.10'
LEKTOR_IMAGE = f'{IMAGE}-lektor'
PROXY_IMAGE = f'{IMAGE}-proxy'
PROXY_CONTAINER = PROXY_IMAGE


def get_config(ctx, env, cfg, auth, network):
    if env is None:
        env = ' '.join(
            f'-e {k}={v}'
            for k, v in
            ctx.get('env', {}).items()
        )
    if cfg is None:
        cfg = ctx['cfg']
    if auth is None:
        auth = ctx['auth']
    network = network or ctx.get('network')
    return env, cfg, auth, network


@task
def dev(ctx):
    ctx.run('pip install -e .[dev,inv]')


@task
def test(ctx):
    ctx.run('pytest -rxXs')


@task
def flake(ctx):
    ctx.run('flake8 src tests')


@task(dev, test, flake)
def clean(ctx):
    pass


@task(test, flake)
def full(c):
    pass


@task
def build_lektor_image(ctx):
    lektor_dir = f'{CONTAINERS_BASE}/lektor'
    ctx.run((
        'docker build '
        f'--build-arg BASE_IMAGE={LEKTOR_BASE} '
        f'--tag {LEKTOR_IMAGE} {lektor_dir}'
    ))


@task
def build_proxy_image(ctx, server_name=None):
    if server_name is None:
        server_name = ctx['server-name']
    proxy_dir = f'{CONTAINERS_BASE}/proxy'
    ctx.run((
        'docker build '
        f'--build-arg BASE_IMAGE={PROXY_BASE} '
        f'--build-arg SERVER_NAME={server_name} '
        f'--tag {PROXY_IMAGE} {proxy_dir}'
    ))


@task
def run_proxy(ctx, network=None):
    *_, network = get_config(ctx, None, None, None, network)
    ctx.run(f'docker kill {PROXY_CONTAINER}', warn=True)
    ctx.run(f'docker rm {PROXY_CONTAINER}', warn=True)
    ctx.run((
        f'docker run '
        f'-d --restart unless-stopped '
        f'--net {network} '
        f'--name {PROXY_CONTAINER} '
        f'{PROXY_IMAGE} '
    ))


@task
def build_server_image(ctx):
    server_dir = f'{CONTAINERS_BASE}/server'
    ctx.run(f'rm {server_dir}/lektorium*.whl', warn=True)
    ctx.run(f'pip wheel -w {server_dir} --no-deps .')
    ctx.run((
        f'docker build '
        f'--tag {IMAGE} {server_dir}'
    ))


@task(build_lektor_image, build_server_image)
def build(ctx):
    pass


@task
def local(ctx, cfg=None, auth=None):
    _, cfg, auth, _ = get_config(ctx, None, cfg, auth, None)
    ctx.run(f'python -m lektorium {cfg} {auth}')


@task
def run(
    ctx,
    create_options='--restart unless-stopped',
    start_options=None,
    env=None,
    cfg=None,
    auth=None,
    network=None,
):
    env, cfg, auth, network = get_config(ctx, env, cfg, auth, network)
    ctx.run(f'docker stop {CONTAINER}', warn=True)
    ctx.run(f'docker kill {CONTAINER}', warn=True)
    ctx.run(f'docker rm {CONTAINER}', warn=True)
    ctx.run((
        f'docker create {create_options} {env} '
        f'--name {CONTAINER} '
        f'--net {network} '
        f'-v /sessions '
        f'-v /var/run/docker.sock:/var/run/docker.sock '
        f'{IMAGE} '
        f'{cfg} {auth}'
    ))
    ctx.run(f'docker network connect bridge {CONTAINER}')
    ctx.run(f'docker start {start_options} {CONTAINER}')


@task
def debug(ctx, env=None, cfg=None, auth=None, network=None):
    env, cfg, auth, network = get_config(ctx, env, cfg, auth, network)
    call(
        run,
        create_options='-ti --rm',
        start_options='-i',
        env=env,
        cfg=cfg,
        auth=auth,
        network=network,
    )
