#!/usr/bin/with-contenv bashio
if bashio::services.available "mqtt"; then
  export MQTT_HOST="$(bashio::services mqtt host)"
  export MQTT_PORT="$(bashio::services mqtt port)"
  export MQTT_USER="$(bashio::services mqtt username)"
  export MQTT_PASS="$(bashio::services mqtt password)"
else
  bashio::log.warning "Kein MQTT-Broker gefunden (Mosquitto installieren) - Auswahlliste und Knopf in Home Assistant fehlen, das Logbuch geht trotzdem."
fi
exec python3 -u /app/greport.py
