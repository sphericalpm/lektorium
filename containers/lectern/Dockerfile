ARG BASE_IMAGE
FROM $BASE_IMAGE
ARG PIP_EXTRA_INDEX_URL
RUN apk -U add --no-cache git python3 python3-dev openssl-dev gcc musl-dev libffi-dev cargo npm \
    && python3 -m venv env \
    && source ./env/bin/activate \
    && pip install --upgrade pip && pip install --upgrade wheel setuptools \
    && PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL pip install lectern-iarc-ui \
    && rm -rf /root/.cache
ENV PATH="/env/bin:$PATH"
ENTRYPOINT ["lectern-ui"]
