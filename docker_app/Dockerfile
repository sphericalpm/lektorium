FROM ubuntu:18.04

# get updates and upgrades
RUN apt update && apt upgrade -y

# install python 3
RUN apt install imagemagick python3 python3-pip python3-dev libssl-dev libffi-dev -y

# setup locales
RUN apt install locales -y && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# create workdir
WORKDIR /lektor_site_folder

# get site path
ARG site_dir

# copy site in container
COPY $site_dir .

# install lektor
RUN pip3 install Lektor

# open 5000 port TODO: change port to other from arg
EXPOSE 5000

# run container with site
CMD ["lektor", "server"]
