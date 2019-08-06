import re
import datetime
import typing

import docker  # type: ignore
from docker.models import images, containers  # type: ignore

client = docker.from_env()

print(client.containers.list(all=True))
print(client.images.list())


"""
Images
"""


def get_images() -> typing.List[images.Image]:
    """
    Return the list of available image objects

    :return: List of image objects
    """
    all_images = client.images.list()

    return all_images


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

    datetime_now = datetime.datetime.now()
    # build a new image for the selected website
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


def run_container(image: images.Image) -> containers.Container:
    """
    Return a list of available container objects

    :return: List of container objects
    """
    started_container = client.containers.run(
        image=image, auto_remove=True, detach=True, network_mode="host"
    )

    return started_container


def get_containers() -> typing.List[containers.Container]:
    """
    Return list of available Containers-obects

    :return: List with containers objects
    """
    all_containers = client.containers.list(all=True)

    return all_containers


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
    container.stop(timeout=20)


def pause_container(container: containers.Container) -> None:
    """
    Pause selected container;

    :param container: Container object for pause
    """
    container.pause()


def unpause_container(container: containers.Container) -> None:
    """
    Un-pause selected container;

    :param container: Container object to un-pause
    """
    container.unpause()


"""
Other methods
"""


def prune() -> None:
    """
    Delete unused images and containers.
    """
    client.containers.prune()
    client.images.prune()


prune()

new_image, logs = build_new_image(
    site_name="lektor site number first", site_dir="t_sites/LctrmTestSite1/"
)

new_container = run_container(image=new_image)

print(new_container)

stop_container(new_container)
delete_container(new_container)
