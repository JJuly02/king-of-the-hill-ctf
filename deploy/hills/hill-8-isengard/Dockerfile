FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends procps libcap2-bin \
    && rm -rf /var/lib/apt/lists/*
COPY server.py reset.sh /opt/app/
RUN chmod +x /opt/app/reset.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
