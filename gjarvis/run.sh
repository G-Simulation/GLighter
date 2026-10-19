#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

if bashio::services.available "mqtt"; then
    export MQTT_HOST="$(bashio::services mqtt 'host')"
    export MQTT_PORT="$(bashio::services mqtt 'port')"
    export MQTT_USER="$(bashio::services mqtt 'username')"
    export MQTT_PASSWORD="$(bashio::services mqtt 'password')"
    bashio::log.info "MQTT gefunden: ${MQTT_HOST}:${MQTT_PORT}"
else
    bashio::log.warning "Kein MQTT-Broker gefunden – Lärmprotokoll-Pause ist deaktiviert."
fi

bashio::log.info "Starte GJarvis ..."
exec python3 -u /gjarvis.py
