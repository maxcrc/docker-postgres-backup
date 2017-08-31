#!/bin/bash

DATE=$(date +%Y%m%d%H%M)
FILE_NAME="${PG_DATABASE}-database-${DATE}.backup"
PG_BACKUP_FOLDER="/var/lib/backups"

set -e

test -f ~/.pgpass || { echo "${PG_HOSTNAME}:${PG_PORT}:${PG_DATABASE}:${PG_USER}:${PG_PASSWORD}" > ~/.pgpass && chmod 0600 ~/.pgpass; }

test -d "${PG_BACKUP_FOLDER}" || mkdir "${PG_BACKUP_FOLDER}"
{ [ $# -gt 0 ] && exec "$@"; } && exit $?

echo "Operating on '${PG_HOSTNAME}:${PG_PORT}' and db: '${PG_DATABASE}' as user '${PG_USER}'"

echo "[$(date -Iseconds)] Running vacuumdb."
vacuumdb -h "${PG_HOSTNAME}" -U "${PG_USER}" -d "${PG_DATABASE}"

echo "REMOVE_OLD_BACKUPS = ${REMOVE_OLD_BACKUPS}"

if [[ $REMOVE_OLD_BACKUPS == 1 ]]
then
	echo "REMOVE_OLD_BACKUPS = ${REMOVE_OLD_BACKUPS}"
	/usr/bin/python3 /removeoldbackups.py -vv "${PG_BACKUP_FOLDER}"
fi

echo -e "[$(date -Iseconds)] Running pg_dump."
pg_dump -h "${PG_HOSTNAME}" -U "${PG_USER}" -Fc "${PG_DATABASE}" --no-owner > "${PG_BACKUP_FOLDER}/${FILE_NAME}"
