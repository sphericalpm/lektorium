FROM ubuntu:bionic
RUN apt-get update \
    && apt-get -y install python3 python3-venv locales \
    && locale-gen en_US.UTF-8 \
    && python3 -m venv env \
    && rm -rf \
        /var/lib/apt/* \
        /var/log/apt/* \
        /var/cache/apt/* \
        /usr/lib/python3.6/__pycache__
ADD lektorium*whl /
RUN LC_ALL=en_US.UTF-8 PATH="/env/bin:$PATH" pip install --no-cache *whl \
    && LC_ALL=en_US.UTF-8 PATH="/env/bin:$PATH" python -m lektorium.install \
    && rm -rf \
        /usr/lib/python3.6/__pycache__ \
        /root/.npm
ENV LC_ALL en_US.UTF-8
ENV PATH "/env/bin:$PATH"
CMD ["/env/bin/python", "-m", "lektorium"]
