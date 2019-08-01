import re
import datetime
import typing

import docker  # type: ignore
from docker.models import images, containers  # type: ignore

client = docker.from_env()

print(client.containers.list(all=True))
print(client.images.list(all=True))


"""
Images
"""


def build_new_image(
    site_name: str, site_dir: str
) -> typing.Tuple[images.Image, typing.Iterable]:
    """
    Build new image from src

    :param site_name: Site name which will be used in image tag

    :return: Tuple with image object and logs.
    """
    # clean site name from invalid symbols
    clean_site_name = re.sub(
        r'[ !"#$%&()*+,./:;<=>?@[\]^`{|}~]', "_", site_name
    ).lower()
    # get current datetime
    datetime_now = datetime.datetime.now()
    # build new image for selected website
    result_image, logs_data = client.images.build(
        path=".",
        dockerfile="docker_app/Dockerfile",
        tag=f"{clean_site_name}_{datetime_now.strftime('%-Hh-%-Mm-%-Ss')}:{datetime_now.strftime('%Y.%m.%d')}",
        quiet=True,
        buildargs={"site_dir": site_dir},
        # TODO change to True
        nocache=False,
        rm=True,
        forcerm=True,
    )
    return result_image, logs_data


def delete_image(image: str) -> None:
    """
    Delete selected image;

    :param image: Image ID(short or long)
    """
    client.images.remove(image=image, force=True)


"""
Containers
"""


def delete_container(container: containers.Container) -> None:
    """
    Delete selected container;

    :param container: Container object for deleting
    """
    container.remove(force=True)


def stop_container(container: containers.Container) -> None:
    """
    Stop selected container;

    :param container: Container object for stoping
    """
    container.stop()


"""
Other methods
"""


def prune_data() -> None:
    """
    Delete unused images and containers.
    """
    client.containers.prune()
    client.images.prune()


prune_data()

res = build_new_image(
    site_name="lector site number first", site_dir="t_sites/LctrmTestSite1/"
)

print(res[0])
print(res[1])
