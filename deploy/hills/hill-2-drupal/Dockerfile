FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends bash procps && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash www
COPY server.py reset.sh /opt/app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /opt/app/reset.sh
EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
