FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends sudo tar procps && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/sh jenkins || true
COPY server.py sudoers.golden reset.sh /opt/app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /opt/app/reset.sh
EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
