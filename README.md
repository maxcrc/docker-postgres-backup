# maxcrc/postgres-backup

Container will start and do the backup of db of the linked postgres server.

## Short example:

```bash
sudo docker run -d --link postgressql \
                    -e PG_USER=SomeUser \
                    -e PG_PASSWORD=SomePassword \
                    -e PG_DATABASE=SomeDatabase \
                    -v /var/lib/postgresql/data/backups:/var/lib/postgresql/data/backups \
                    maxcrc/postgres-backup
```
