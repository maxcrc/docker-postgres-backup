FROM debian:stretch

ENV PG_VERSION=9.6 PG_USER=USER PG_PASSWORD=PASSWORD PG_DATABASE=DATABASE PG_PORT=5432 REMOVE_OLD_BACKUPS=0 PG_HOSTNAME="postgresql"

RUN apt-get update && \
	apt-get install wget ca-certificates lsb-release gnupg -y --no-install-recommends && \
	wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
	echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
	apt-get update && \
	apt-get install postgresql-client-${PG_VERSION} python3-minimal -y --no-install-recommends

RUN apt-get purge wget ca-certificates lsb-release gnupg -y && \
	apt-get clean && \
	apt-get autoremove -y && \
	rm -rf /var/lib/apt/lists/*

ADD entrypoint.sh removeoldbackups/removeoldbackups.py /

VOLUME ["/var/lib/postgresql/data/backups"]

ENTRYPOINT ["/entrypoint.sh"]

