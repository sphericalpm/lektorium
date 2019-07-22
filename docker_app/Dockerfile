FROM ubuntu:18.04

RUN apt update && apt install upgrades -y

RUN apt install python3 python3-pip -y

WORKDIR /website_folder

ADD t1 t1

RUN ls

RUN cd t1 && pip3 install -r requirements.txt
