import re
import datetime
import typing

import docker  # type: ignore
from docker.models import images, containers  # type: ignore


class DockerModule:
    def __init__(self):
        """
        Connect to local docker and create docker-client
        """
        self.client = docker.from_env()

    def close(self) -> None:
        """
        Close docker-client connestion
        """
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if exc_value:
            raise

    """
    Images
    """

    def get_images(self) -> typing.List[images.Image]:
        """
        Return the list of available image objects

        :return: List of image objects
        """
        all_images = self.client.images.list()

        return all_images

    def build_new_image(
        self, site_name: str, site_dir: str
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
        result_image, logs_data = self.client.images.build(
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

    def delete_image(self, image: str) -> None:
        """
        Delete selected image;

        :param image: Image ID(short or long)
        """
        self.client.images.remove(image=image, force=True)

    """
    Containers
    """

    def run_container(self, image: images.Image) -> containers.Container:
        """
        Return a list of available container objects

        :return: List of container objects
        """
        started_container = self.client.containers.run(
            image=image, auto_remove=True, detach=True, network_mode="host"
        )

        return started_container

    def get_containers(self) -> typing.List[containers.Container]:
        """
        Return a list of available containers objects

        :return: List of container objects
        """
        all_containers = self.client.containers.list(all=True)

        return all_containers

    def delete_container(self, container: containers.Container) -> None:
        """
        Delete selected container;

        :param container: Container object for deleting
        """
        container.remove(force=True)

    def stop_container(self, container: containers.Container) -> None:
        """
        Stop selected container;

        :param container: Container object for stopping
        """
        container.stop(timeout=20)

    def pause_container(self, container: containers.Container) -> None:
        """
        Pause selected container;

        :param container: Container object to pause
        """
        container.pause()

    def unpause_container(self, container: containers.Container) -> None:
        """
        Un-pause selected container;

        :param container: Container object to un-pause
        """
        container.unpause()

    """
    Other methods
    """

    def prune(self) -> None:
        """
        Delete unused images and containers.
        """
        self.client.containers.prune()
        self.client.images.prune()
