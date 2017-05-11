FROM debian:stretch

ENV PG_VERSION=9.5 PG_USER=USER PG_PASSWORD=PASSWORD PG_DATABASE=DATABASE PG_PORT=5432 BACKUP_KEEP_DAYS=30

RUN apt-get update && \
	apt-get install wget ca-certificates lsb-release gnupg -y --no-install-recommends && \
	wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
	echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
	
RUN apt-get update && \
	apt-get install wget ca-certificates postgresql-client-${PG_VERSION} -y --no-install-recommends && \
	rm -rf /var/lib/apt/lists/*


ADD entrypoint.sh /

VOLUME ["/var/lib/postgresql/data/backups"]

ENTRYPOINT ["/entrypoint.sh"]

