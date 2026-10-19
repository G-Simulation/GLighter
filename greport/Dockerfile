ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.21
FROM $BUILD_FROM
RUN apk add --no-cache python3 py3-paho-mqtt py3-websocket-client
COPY run.sh /run.sh
COPY app /app
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
