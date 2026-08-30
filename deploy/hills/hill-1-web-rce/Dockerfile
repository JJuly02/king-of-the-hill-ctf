FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends sudo iputils-ping procps \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/sh www
COPY server.py sudoers.golden reset.sh /opt/app/
RUN chmod +x /opt/app/reset.sh
COPY entrypoint.sh /entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
