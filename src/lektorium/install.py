import atexit
import contextlib
try:
    import importlib.resources as importlib_resources
except ModuleNotFoundError:
    import importlib_resources
import lektorium


def install():
    path = importlib_resources.path(lektorium.__name__, 'client')
    closer = contextlib.ExitStack()
    path = closer.enter_context(path)
    if (path / 'build').exists():
        atexit.register(closer.close)
        return (path / 'build')
    raise NotImplementedError()


if __name__ == '__main__':
    install()
