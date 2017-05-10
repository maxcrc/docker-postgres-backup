#!/bin/bash

DATE=$(date +%Y%m%d%H%M)
FILE_NAME="${PG_DATABASE}-database-${DATE}.backup"
POSTGRES_FOLDER="/var/lib/postgresql"


if [ ! -d "${POSTGRES_FOLDER}" ]
then
   mkdir -p ${POSTGRES_FOLDER}
fi

echo postgres:${PG_PORT}:${PG_DATABASE}:${PG_USER}:${PG_PASSWORD} > ~/.pgpass && chmod 0600 ~/.pgpass

cat ~/.pgpass

pg_dump -h postgres -U "${PG_USER}" -Fc "${PG_DATABASE}" --no-owner > ${POSTGRES_FOLDER}/${FILE_NAME}
