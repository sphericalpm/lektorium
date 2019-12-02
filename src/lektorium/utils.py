import atexit
import contextlib
import shlex


def flatten_options(labels, prefix=''):
    """Converts hierarchical list of dot separated options to dict of flat one.

    This structure:
    {'aaa':'b(`f`)','ccc.rrr':{'ddd':'eee',}}
    will be converted to:
    {'traefik.aaa': 'b(`f`)', 'traefik.ccc.rrr.ddd': 'eee'}
    """
    def flatten(labels, prefix):
        for k, v in labels.items():
            name = f'{prefix}{prefix and "."}{k}'
            if isinstance(v, dict):
                yield from flatten(v, name)
            else:
                yield name, v
    return dict(flatten(labels, prefix))


def named_args(name, dct):
    """This function converts dict of named args to string for
    use in command line (f.e. env or label docker params).

    This structure:
    {'traefik.aaa': 'b(`f`)', 'traefik.ccc.rrr.ddd': 'eee'}
    will be converted to:
    "--label traefik.aaa='b(`f`)' --label traefik.ccc.rrr.ddd=eee"
    """
    return ' '.join(f'{name} {k}={shlex.quote(v)}' for k, v in dct.items())


def closer(manager):
    closer = contextlib.ExitStack()
    result = closer.enter_context(manager)
    atexit.register(closer.close)
    return result
