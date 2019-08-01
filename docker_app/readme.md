1. Custom image build:
    ```bash
    sudo docker build --build-arg site_dir=<path to Lektor dir> -f docker_app/Dockerfile .
    ```
1. Custom container run:
    ```bash
    sudo docker run --network="host" -d <image name>:<image tag>
    ```