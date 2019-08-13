import itertools
from docker.models import images, containers

from docker_app.main import DockerModule


class TestDockerInterface:
    def setup(self):
        self.docker_module = DockerModule()
        self.image_name = "Lektor test site"
        self.site_path = "tests/LektorTestSite1/"

    """
    Images
    """

    def test_get_images(self):
        with self.docker_module as docker_client:
            all_images = docker_client.get_images()
            assert type(all_images) == list

    def test_build_image(self):
        with self.docker_module as docker_client:
            result = docker_client.build_new_image(
                site_name=self.image_name, site_dir=self.site_path
            )
            assert type(result) == tuple
            assert len(result) == 2
            assert type(result[0]) == images.Image
            assert type(result[1]) == itertools._tee

    def test_delete_image(self):
        with self.docker_module as docker_client:
            # create new image
            new_image, _ = docker_client.build_new_image(
                site_name=self.image_name, site_dir=self.site_path
            )
            # get actually images list
            old_all_images = docker_client.get_images()
            assert new_image in old_all_images
            # delete created image
            docker_client.delete_image(image=new_image.id)
            # get new actually images list
            new_all_images = docker_client.get_images()
            assert new_image not in new_all_images

    """
    Containers
    """
    # TODO add container status check
    def test_run_container(self):
        with self.docker_module as docker_client:
            # create new image
            new_image, _ = docker_client.build_new_image(
                site_name=self.image_name, site_dir=self.site_path
            )
            # run new image as container
            new_container = docker_client.run_container(image=new_image)
            containers_list = docker_client.get_containers()
            assert type(new_container) == containers.Container
            assert new_container in containers_list

    def test_get_containers(self):
        with self.docker_module as docker_client:
            all_containers = docker_client.get_containers()
            assert type(all_containers) == list

    def test_stop_container(self):
        with self.docker_module as docker_client:
            # create new image
            new_image, _ = docker_client.build_new_image(
                site_name=self.image_name, site_dir=self.site_path
            )
            # run new image as container
            new_container = docker_client.run_container(image=new_image)
            # get actually containers list
            old_all_containers = docker_client.get_containers()
            assert new_container in old_all_containers
            # delete stop container
            docker_client.stop_container(container=new_container)
            # get new actually containers list
            new_all_containers = docker_client.get_containers()
            assert new_container not in new_all_containers
