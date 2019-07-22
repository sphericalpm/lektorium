import re
import datetime

import docker

client = docker.from_env()

# print(client.containers.list(all=True))
# print(client.images.list(all=True))


def build_new_image(site_name: str, site_dir: str):
    """
    Build new image from src

    :param site_name: Site name which will be used in image tag

    :return: List with image object and logs.
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
        # TODO change to True
        nocache=False,
        rm=True,
        forcerm=True,
    )
    return result_image, logs_data


def clean_data():
    """
    Delete unused images and containers.
    """
    client.containers.prune()
    client.images.prune()


clean_data()
res = build_new_image(site_name="TestFuckingSite", site_dir="some qute dir")

print(res[0])
print(res[1])
