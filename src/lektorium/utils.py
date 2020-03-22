import atexit
import contextlib


def closer(manager):
    closer = contextlib.ExitStack()
    result = closer.enter_context(manager)
    atexit.register(closer.close)
    return result
