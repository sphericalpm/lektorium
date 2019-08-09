import pytest

from docker_app import main


class BaseTest:
    def setUp(self):
        self.dk_client = main.client

    def tearDown(self):
        self.dk_client.close()

    def test_get_images(self):
        all_images = main.get_images()
        assert type(all_images)==list
