ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.21
FROM $BUILD_FROM
RUN apk add --no-cache python3 py3-numpy py3-paho-mqtt alsa-utils alsa-plugins-pulse openssl \
 && (apk add --no-cache ffmpeg || echo "Hinweis: ffmpeg nicht verfuegbar, Stream-Quellen deaktiviert") \
 && (apk add --no-cache pulseaudio-utils || echo "Hinweis: pulseaudio-utils nicht verfuegbar, Quellenauswahl eingeschraenkt") \
 && (apk add --no-cache py3-scipy || echo "Hinweis: scipy nicht verfuegbar, Brummfilter abgeschaltet")
COPY run.sh /run.sh
COPY app /app
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
