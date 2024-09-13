ARG BASE_IMAGE
FROM $BASE_IMAGE
RUN apk -U add --no-cache python3 python3-dev openssl-dev gcc musl-dev libffi-dev cargo \
    && python3 -m venv env \
    && PATH="/env/bin:$PATH" pip install --no-cache "lektor==3.2.0" "markupsafe==2.0.1" pytz \
    && rm -rf /root/.cache
ENV PATH "/env/bin:$PATH"
ENTRYPOINT ["lektor"]
