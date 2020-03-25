FROM ubuntu:bionic
RUN ( \
        [ "$(. /etc/os-release; echo $ID)" != "ubuntu" ] || { \
            grep universe$ /etc/apt/sources.list || \
            head -1 /etc/apt/sources.list | \
            sed 's/ [a-zA-Z]*$/ universe/' >>/etc/apt/sources.list; \
        } \
    ) \
    && apt-get update \
    && apt-get -y install python3 python3-venv locales openssh-client git \
    && locale-gen en_US.UTF-8 \
    && python3 -m venv env \
    && rm -rf \
        /var/lib/apt/* \
        /var/log/apt/* \
        /var/cache/apt/* \
        /usr/lib/python3.6/__pycache__
ADD lektorium*whl /
ADD key /root/.ssh/id_rsa
ADD entrypoint.sh /
RUN chmod 700 /root/.ssh \
    && chmod 600 /root/.ssh/id_rsa \
    && LC_ALL=en_US.UTF-8 PATH="/env/bin:$PATH" pip install --no-cache *whl \
    && rm -rf \
        /usr/lib/python3.6/__pycache__ \
        /root/.npm
ENV LC_ALL en_US.UTF-8
ENV PATH "/env/bin:$PATH"
VOLUME /sessions
ENTRYPOINT ["/entrypoint.sh"]
