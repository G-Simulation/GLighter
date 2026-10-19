# Basis: Debian (Multi-Arch, amd64 + arm64) – Format für Home-Assistant-Apps ab 2026 (ohne build.yaml)
ARG BUILD_FROM=ghcr.io/home-assistant/base-debian:bookworm
FROM ${BUILD_FROM}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 python3-venv pulseaudio-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir --no-deps openwakeword==0.6.0

COPY gjarvis.py web.py features.py apps.py lizenz.py satellite.py config.yaml /
COPY web /web
COPY translations /translations
COPY run.sh /run.sh
RUN chmod a+x /run.sh

LABEL \
    org.opencontainers.image.title="Home Assistant App: GJarvis" \
    org.opencontainers.image.description="Deutscher Sprachassistent Jarvis für Home Assistant" \
    org.opencontainers.image.source="https://github.com/G-Simulation/GSimulations-HomeAssistant" \
    org.opencontainers.image.vendor="G-Simulation"

CMD [ "/run.sh" ]
