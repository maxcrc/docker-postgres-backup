#!/bin/bash

DATE=$(date +%Y%m%d%H%M)
FILE_NAME="${PG_DATABASE}-database-${DATE}.backup"
POSTGRES_FOLDER_BACKUP="/var/lib/postgresql/data/backups"
POSTGRES_HOSTNAME="postgresql"

test -f ~/.pgpass || { echo "${POSTGRES_HOSTNAME}:${PG_PORT}:${PG_DATABASE}:${PG_USER}:${PG_PASSWORD}" > ~/.pgpass && chmod 0600 ~/.pgpass; }

test -d "${POSTGRES_FOLDER_BACKUP}" || mkdir "${POSTGRES_FOLDER_BACKUP}"
{ [ $# -gt 0 ] && exec "$@"; } && exit $?

echo "Operating on '${POSTGRES_HOSTNAME}:${PG_PORT}' and db: '${PG_DATABASE}' as user '${PG_USER}'"

echo "[$(date -Iseconds)] Running vacuumdb."
vacuumdb -h "${POSTGRES_HOSTNAME}" -U "${PG_USER}" -d "${PG_DATABASE}"

echo "[$(date -Iseconds)] Removing backups older than ${BACKUP_KEEP_DAYS} days."
find "${POSTGRES_FOLDER_BACKUP}/" -name *.backup -mtime +${BACKUP_KEEP_DAYS} -exec rm {} \;

echo -e "[$(date -Iseconds)] Running pg_dump."
pg_dump -h "${POSTGRES_HOSTNAME}" -U "${PG_USER}" -Fc "${PG_DATABASE}" --no-owner > "${POSTGRES_FOLDER_BACKUP}/${FILE_NAME}"
