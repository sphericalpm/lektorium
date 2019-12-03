ARG BASE_IMAGE
FROM $BASE_IMAGE
RUN apk -U add nginx \
    && rm /var/cache/apk/APKINDEX* \
    && mkdir /run/nginx /logs \
EXPOSE 80
WORKDIR /
ARG SERVER_NAME
ENV SERVER_NAME ${SERVER_NAME}
COPY nginx.conf /nginx.conf
RUN sed -i'' "s/ENV_SERVER_NAME/$SERVER_NAME/" nginx.conf
CMD nginx -c /nginx.conf -p / -g "daemon off; error_log /dev/stdout debug; pid /dev/null;"
