import os
import pathlib
import shlex
import subprocess
import webbrowser
from invoke import task
from invoke.tasks import call
from lektorium.utils import flatten_options, named_args


CONTAINERS_BASE = 'containers'
IMAGE = 'lektorium'
CONTAINER = IMAGE
LEKTOR_BASE = PROXY_BASE = 'alpine:v3.10'
LEKTOR_IMAGE = f'{IMAGE}-lektor'
PROXY_IMAGE = f'{IMAGE}-proxy'
PROXY_CONTAINER = PROXY_IMAGE


def get_config(ctx, env, cfg, auth, network):
    if env is None:
        env = named_args('-e', ctx.get('env', {}))
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
def cov(ctx):
    ctx.run('pytest --cov=lektorium --cov-report=html')
    path = (pathlib.Path('.') / 'htmlcov' / 'index.html').resolve()
    webbrowser.open(f"file://{path}")


@task
def flake(ctx):
    ctx.run('flake8 src tests')


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
def build_nginx_image(ctx, server_name=None):
    if server_name is None:
        server_name = ctx['server-name']
    proxy_dir = f'{CONTAINERS_BASE}/nginx-proxy'
    ctx.run((
        'docker build '
        f'--build-arg BASE_IMAGE={PROXY_BASE} '
        f'--build-arg SERVER_NAME={server_name} '
        f'--tag {PROXY_IMAGE} {proxy_dir}'
    ))


def lektorium_labels(server_name, port=80):
    labels = {
        'enable': 'true',
        'http.services.lektorium.loadbalancer.server.port': f'{port}',
        'http.middlewares.lektorium-redir.redirectscheme.scheme': 'https',
        'http.routers': {
            'lektorium' : {
                'entrypoints': 'websecure',
                'rule': f"Host(`{server_name}`)",
                'tls.certresolver': 'le',
            },
        },
    }
    return named_args("--label", flatten_options(labels, "traefik"))


@task
def run_nginx(ctx, network=None):
    *_, network = get_config(ctx, None, None, None, network)
    ctx.run(f'docker kill {PROXY_CONTAINER}', warn=True)
    ctx.run(f'docker rm {PROXY_CONTAINER}', warn=True)
    ctx.run((
        f'docker run '
        f'-d --restart unless-stopped '
        f'--net {network} '
        f'--name {PROXY_CONTAINER} '
        f'{lektorium_labels(ctx["server-name"])} '
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
        f'-v lektorium-sessions:/sessions '
        f'-v /var/run/docker.sock:/var/run/docker.sock '
        f'{lektorium_labels(ctx["server-name"], 8000)} '
        f'{IMAGE} '
        f'{cfg} {auth}'
    ))
    ctx.run(f'docker network connect bridge {CONTAINER}')
    ctx.run(f'docker start {start_options or ""} {CONTAINER}')


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


@task
def list(ctx):
    proc = subprocess.Popen(
        'python -u -m lektorium LIST',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
    )
    target = None
    for line in proc.stdout:
        print(line.decode().rstrip())
        if b'Running on' in line:
            target = line[20:-10].decode()
            break
    if target is not None:
        webbrowser.open(target)
    try:
        proc.communicate()
    except:
        proc.kill()
        proc.wait()
