ARG BASE_IMAGE
FROM $BASE_IMAGE
RUN apk -U add --no-cache openssl-dev gcc musl-dev libffi-dev \
    && apk add --no-cache python3 python3-dev \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && ln -s /usr/bin/pip3 /usr/bin/pip \
    && pip --no-cache install --upgrade pip lektor \
    && rm -rf /root/.cache
ENTRYPOINT ["lektor"]
