#!/usr/bin/env python2
from datetime import datetime
import subprocess
from os import path, makedirs
from utils import log

class Backuper():
    def __init__(self, db, backup_path, user=None, host=None):
        self.db = db
        self.backup_path = backup_path
        self.user = user
        self.host = host

    def do_backup_impl(self):
        timeslot = datetime.now().strftime('%Y%m%d%H%M')
        backup_file = path.join(self.backup_path, "{}-database-{}.backup".format(self.db, timeslot))

        vacuumdb_args = ['/usr/bin/vacuumdb', '-d', self.db]
        pg_dump_args = ['/usr/bin/pg_dump', '-Fc', '-b', self.db, '-f', '--no-owner', backup_file]

        if self.host:
            vacuumdb_args.extend(["-h", self.host])
            pg_dump_args.extend(["-h", self.host])

        if self.user:
            vacuumdb_args.extend(["-U", self.user])
            pg_dump_args.extend(["-U", self.user])

        log.info("Running vacuum on the database.")
        subprocess.call(vacuumdb_args)

        log.info("Running pg_dump on the database.")
        subprocess.call(pg_dump_args)

        log.info("Backup and Vacuum complete for database '{}'".format(self.db))

        return backup_file

    def backup(self):
        if not path.exists(self.backup_path):
            print("Base folder {} doesn't exists. Creating".format(path.dirname(self.backup_path)))
            try:
                makedirs(self.backup_path)
            except OSError as exc:
                print('Can\'t create {}. Exception: {}'.format(self.backup_path, exc))
                exit(1)

        message = str()
        try:
            backup_path = self.do_backup_impl()

        except Exception as e:
            log.error('Exception occured. Exception: {}'.format(e.message))
        finally:
            message = ["Subject:Odoo db backup finished\n\n", ]

        return backup_path

