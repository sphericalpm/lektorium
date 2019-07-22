FROM ubuntu:18.04

RUN apt update && apt upgrade -y

RUN apt install python3 python3-pip -y

WORKDIR /lektor_site_folder

# t_sites/t1 - will be changed to site path from config file
ADD t_sites/t1 site/

# install site requirements
RUN cd site/ && pip3 install -r requirements.txt

# run site
CMD ["echo", "Hello from site!"]