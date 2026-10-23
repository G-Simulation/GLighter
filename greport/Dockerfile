ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.21
FROM $BUILD_FROM
RUN apk add --no-cache python3 py3-paho-mqtt py3-websocket-client
# Texterkennung für Anlagen (offline): PDF-Text (poppler-utils), Bilder und Scans (tesseract, Deutsch und Englisch), HEIC-Fotos.
# Fehlt ein Paket, läuft GReport trotzdem – die Erkennung meldet dann, was fehlt.
RUN apk add --no-cache poppler-utils || echo "poppler-utils nicht verfügbar – PDF-Text wird nicht erkannt"
RUN apk add --no-cache tesseract-ocr tesseract-ocr-data-deu tesseract-ocr-data-eng || echo "tesseract nicht verfügbar – keine Texterkennung in Bildern"
RUN apk add --no-cache libheif-tools || echo "libheif-tools nicht verfügbar – HEIC-Fotos werden nicht gelesen"
COPY run.sh /run.sh
COPY app /app
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
