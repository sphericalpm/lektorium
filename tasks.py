import os
import pathlib
import subprocess
import webbrowser

from invoke import task
from invoke.tasks import call
from spherical.dev.tasks import clean, dev, flake, isort, test  # noqa: F401
from spherical.dev.utils import flatten_options, named_args


CONTAINERS_BASE = 'containers'
IMAGE = 'lektorium'
CONTAINER = IMAGE
LEKTOR_BASE = PROXY_BASE = 'alpine'
LEKTOR_IMAGE = f'{IMAGE}-lektor'
PROXY_IMAGE = f'{IMAGE}-proxy'
PROXY_CONTAINER = PROXY_IMAGE


def get_config(ctx, env, cfg, auth, network):
    if env is None:
        env = named_args('-e ', ctx.get('env', {}))
    if cfg is None:
        cfg = ctx['cfg']
        cfg = f'{cfg["repo"]}:{",".join(cfg["server"])}'
    if auth is None:
        auth = ctx.get('auth', None)
        if auth is not None:
            auth = ','.join(auth)
    network = network or ctx.get('network')
    return env, cfg, auth, network


def get_skip_resolver(ctx):
    return ctx.get('env', {}).get('LEKTORIUM_SKIP_RESOLVER', False)


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


def lektorium_labels(server_name, port=80, skip_resolver=False):
    labels = {
        'enable': 'true',
        'http.services.lektorium.loadbalancer.server.port': f'{port}',
        'http.routers': {
            'lektorium': {
                'entrypoints': 'websecure',
                'rule': f"Host(`{server_name}`)",
                'tls': {},
                **({} if skip_resolver else {'tls.certresolver': 'le'}),
            },
        },
    }
    return named_args("--label ", flatten_options(labels, "traefik"))


@task
def run_nginx(ctx, network=None):
    *_, network = get_config(ctx, None, None, None, network)
    ctx.run(f'docker kill {PROXY_CONTAINER}', warn=True)
    ctx.run(f'docker rm {PROXY_CONTAINER}', warn=True)
    labels = lektorium_labels(
        ctx["server-name"],
        skip_resolver=get_skip_resolver(ctx),
    )
    ctx.run((
        f'docker run '
        f'-d --restart unless-stopped '
        f'--net {network} '
        f'--name {PROXY_CONTAINER} '
        f'{labels} '
        f'{PROXY_IMAGE} '
    ))


@task
def run_traefik(ctx, image='traefik', ip=None, network=None):
    if ctx.get('skip-traefik', False):
        return

    env, *_, network = get_config(ctx, None, None, None, network)
    ctx.run(f'docker kill {PROXY_CONTAINER}', warn=True)
    ctx.run(f'docker rm {PROXY_CONTAINER}', warn=True)
    resolver = ''
    cert_options = ''
    volumes = ''
    if get_skip_resolver(ctx):
        volumes = ((
            '-v ./certs/:/etc/certs '
            f'-v {ctx["dev-certs"]["chain"]}:/etc/certs/cert.pem '
            f'-v {ctx["dev-certs"]["key"]}:/etc/certs/key.pem '
        ))
        cert_options = ((
            '--entrypoints.websecure.http.tls=true '
            '--providers.file.filename=/etc/certs/traefik-config.yml '
        ))
    else:
        volumes = '-v traefik-letsencrypt:/letsencrypt '
        resolver = flatten_options(
            ctx['certificate-resolver'],
            'certificatesresolvers.le.acme',
        )
        resolver = named_args('--', resolver)

    labels = {
        'enable': 'true',
        'http': {
            'middlewares': {
                'redirect-to-https.redirectscheme.scheme': 'https',
            },
            'routers': {
                'redirect-to-https': {
                    'entrypoints': 'web',
                    'rule': 'HostRegexp(`{host:.+}`)',
                    'middlewares': 'redirect-to-https',
                },
            },
        },
    }
    labels = named_args('--label ', flatten_options(labels, 'traefik'))

    command = ' '.join([
        'docker create',
        '--restart unless-stopped',
        f'--name {PROXY_CONTAINER}',
        '-v /var/run/docker.sock:/var/run/docker.sock',
        f'{volumes}',
        f'-p {ip or ""}{":" if ip else ""}80:80',
        f'-p {ip or ""}{":" if ip else ""}443:443',
        f'{env}',
        f'{labels}',
        f'{image}',
        '--accessLog',
        '--api.dashboard',
        f'{resolver}',
        '--entrypoints.web.address=:80',
        '--entrypoints.websecure.address=:443',
        '--log.level=DEBUG',
        '--log',
        '--providers.docker.exposedbydefault=false',
        f'{cert_options}',
    ])
    ctx.run(command)
    ctx.run(f'docker network create {network}', warn=True)
    ctx.run(f'docker network connect {network} {PROXY_CONTAINER}')
    ctx.run(f'docker start {PROXY_CONTAINER}')


@task
def build_server_image(ctx):
    if 'key' not in ctx:
        raise RuntimeError('pleas provde key for access server to gitlab')

    server_dir = f'{CONTAINERS_BASE}/server'
    with (pathlib.Path(server_dir) / 'key').open('w') as key_file:
        key = os.linesep.join((
            '-----BEGIN RSA PRIVATE KEY-----',
            *ctx['key'],
            '-----END RSA PRIVATE KEY-----',
            '',
        ))
        key_file.write(key)
    ctx.run(f'rm {server_dir}/lektorium*.whl', warn=True)
    ctx.run(f'pip wheel -w {server_dir} --no-deps .')
    ctx.run((
        f'docker build --tag {IMAGE} '
        f'-f {server_dir}/Dockerfile.ubuntu '
        f'{server_dir}'
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
    labels = lektorium_labels(ctx["server-name"], 8000, get_skip_resolver(ctx))
    ctx.run((
        f'docker create {create_options} {env} '
        f'--name {CONTAINER} '
        f'--net {network} '
        f'-v lektorium-sessions:/sessions '
        f'-v /var/run/docker.sock:/var/run/docker.sock '
        f'{labels} '
        f'{IMAGE} '
        f'{cfg} "{auth}"'
    ))
    ctx.run(f'docker network create {network}', warn=True)
    ctx.run(f'docker network connect {network} {CONTAINER}')
    ctx.run(f'docker start {start_options or ""} {CONTAINER}')


@task(build, run_traefik, run)
def deploy(ctx):
    pass


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
    except Exception:
        proc.kill()
        proc.wait()
