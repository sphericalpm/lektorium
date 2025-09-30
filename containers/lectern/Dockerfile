ARG BASE_IMAGE
FROM $BASE_IMAGE
COPY lectern lectern
COPY lectern-ui-iarc lectern-ui
RUN apk -U add --no-cache git python3 python3-dev openssl-dev gcc musl-dev libffi-dev cargo npm \
    && python3 -m venv env \
    && source ./env/bin/activate \
    && cd lectern && pip install -e ".[dev]" \
    && cd ../lectern-ui && pip install -e ".[dev]" \
    && npx yarn && npx yarn build-only \
    && rm -rf /root/.cache
ENV PATH="/env/bin:$PATH"
WORKDIR /lectern-ui
ENTRYPOINT ["lectern-ui"]
