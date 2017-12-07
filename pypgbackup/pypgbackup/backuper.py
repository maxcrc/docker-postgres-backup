#!/usr/bin/env python2
from datetime import datetime
import subprocess
from os import path, makedirs
from utils import log

class Backuper():
    def __init__(self, db, backup_path, host=None, port=5432, user=None, password=None):
        self._db = db
        self._backup_path = backup_path
        self._user = user
        self._host = host
        self._password = password
        self._port = port

    def _create_auth_file(self):
        with open("~/.pgpass") as pgpass:
            pgpass.write("{}:{}:{}:{}:{}", self._host, self._port, self._db, self._user, self._password)
        
    def do_backup_impl(self):
        timeslot = datetime.now().strftime('%Y%m%d%H%M')
        backup_file = path.join(self._backup_path, "{}-database-{}.backup".format(self._db, timeslot))

        vacuumdb_args = ['/usr/bin/vacuumdb']
        pg_dump_args = ['/usr/bin/pg_dump']

        if self._host:
            vacuumdb_args.extend(["-h", self._host])
            pg_dump_args.extend(["-h", self._host])

        if self._user:
            vacuumdb_args.extend(["-U", self._user])
            pg_dump_args.extend(["-U", self._user])
        
        vacuumdb_args.extend(['-d', self._db])    
        pg_dump_args.extend(['-f', backup_file, '-Fc', self._db, '--no-owner'])

                        
        log.info("Running vacuum on the database. Cmd: {}".format(vacuumdb_args))
        subprocess.call(vacuumdb_args)
        
        
        log.info("Running pg_dump on the database. Cmd: {}".format(pg_dump_args))
        if subprocess.call(pg_dump_args) != 0:
            return None

        log.info("Backup and Vacuum complete for database '{}'".format(self._db))

        return backup_file

    def backup(self):
        if not path.exists(self._backup_path):
            print("Base folder {} doesn't exists. Creating".format(path.dirname(self._backup_path)))
            try:
                makedirs(self._backup_path)
            except OSError as exc:
                print('Can\'t create {}. Exception: {}'.format(self._backup_path, exc))
                exit(1)

        try:
            backup_path = self.do_backup_impl()

        except Exception as e:
            log.error('Exception occured. Exception: {}'.format(e.message))
        finally:
            message = ["Subject:Odoo db backup finished\n\n", ]

        return backup_path

