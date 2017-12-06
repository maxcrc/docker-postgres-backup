#!/usr/bin/env python2
import logging
import calendar
import shutil
import smtplib
from datetime import datetime
import subprocess
from subprocess import Popen, PIPE
from os import path, listdir, remove, makedirs

import paramiko
from dateutil.relativedelta import relativedelta

LOGGER_NAME = "Backup"
LOG_FILE = "backup.log"
_log = logging.getLogger(LOGGER_NAME)

logging.getLogger("paramiko").setLevel(logging.WARNING)

class UploaderFuse:
    def __init__(self, src, dest):
        self._src = src
        self._dest = dest
        super(UploaderFuse, self).__init__(src, dest)

    def upload(self):
        _log.info("Mounting the {} folder".format(self._dest))
        try:
            subprocess.call(['fusermount', '-u', '-z', self._dest])
            subprocess.call(['mount', self._dest])
            shutil.copy2(self._src, self._dest)
            subprocess.call(['fusermount', '-u', self._dest])
        except Exception as e:
            _log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            subprocess.call(['fusermount', '-u', '-z', self._dest])


class UploaderScp(UploaderFuse):
    def __init__(self, src, dest, username, hostname, port=22, dest_file_name=None):
        super(UploaderScp,self).__init__(src, dest)
        self._username = username
        self._hostname = hostname
        self._port = port
        self._dest_file_name = dest_file_name
        self._client = None

    def _connect(self):
        key_filename = path.expanduser(path.join('~', '.ssh', 'id_rsa'))

        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(self._hostname, port=self._port, username=self._username, key_filename=key_filename)

        _log.info('Connecting to \'{}:{}\'. As user: \'{}\'. Using key from \'{}\''.format(self._hostname, self._port, self._username,
                                                                                           key_filename))

    def _disconnect(self):
        if self._client:
            self._client.close()

    def upload(self):
        try:
            _log.info('Uploading backup on {}:{}'.format(self._hostname, self._port))
            if self._dest_file_name:
                dest = path.join(path.dirname(self._dest), self._dest_file_name)

            self._client.open_sftp().put(self._src, dest)
        except Exception as e:
            _log.error('Upload failed. Exception: {}'.format(e))
        finally:
            self._disconnect();

class UploaderSshFs(UploaderFuse):
    def __init__(self, src, dest, mount_point=None):
        super(UploaderSshFs,self).__init__(src, dest)
        self._mount_point = mount_point if mount_point else path.expanduser('~/backup-mnt-point')

    def upload(self):
        _log.info("Mounting the {} folder".format(self._dest))
        try:
            name_host, file_path = self._dest.split(':')
            filename = path.basename(self._src)
            dest = ':'.join([name_host, file_path])

            subprocess.call(['fusermount', '-u', '-z', self._mount_point])

            cmd = 'sshfs {} {} -o IdentityFile={}'.format(dest, self._mount_point, path.expanduser('~/.ssh/id_rsa'))
            c, _, __ = run_process(cmd.split(' '))

            if c != 0:
                raise RuntimeError('Can\'t mount remote FS')

            shutil.copy2(self._src, path.join(self._mount_point, filename))
        except Exception as e:
            _log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            run_process(['fusermount', '-u', '-z', self._mount_point])


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

        _log.info("Running vacuum on the database.")
        subprocess.call(vacuumdb_args)

        _log.info("Running pg_dump on the database.")
        subprocess.call(pg_dump_args)

        _log.info("Backup and Vacuum complete for database '{}'".format(self.db))

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
            _log.error('Exception occured. Exception: {}'.format(e.message))
        finally:
            message = ["Subject:Odoo db backup finished\n\n", ]

        return backup_path


def run_process(args):
    _log.debug('Running command: \'{}\''.format(' '.join(args)))
    process = Popen(args, stdout=PIPE)
    (output, err) = process.communicate()
    return process.wait(), output, err



def clean(backup_folder):
    files = [path.join(backup_folder, f) for f in listdir(backup_folder) if
             path.isfile(path.join(backup_folder, f)) and f.lower().endswith('.backup')]

    def _delete_file(f):
        mtime = datetime.fromtimestamp(path.getmtime(f))
        last_day = calendar.monthrange(mtime.year, mtime.month)[1]
        if mtime < datetime.now() - relativedelta(months=2) and mtime.day != last_day and mtime.day != 1:
            return True
        return False

    _log.info("Removing backups that are older than 60 days and which was not created and start/end of month")

    map(remove, filter(_delete_file, files))


def send_mail(mail_recepients, message):
    server = smtplib.SMTP('smtp.gmail.com:587', timeout=60)
    server.ehlo()
    server.starttls()
    server.login('pp.foss.pp@gmail.com', '123qwerty123')

    for recipient in mail_recepients:
        server.sendmail('pp.foss.pp@gmail.com', recipient, ''.join(message))

    server.quit()

def worker(backuper, uploader=None, cleaner=None, mail_recipients=None):
    lines_start = 0
    message = ""
    if mail_recipients:
        with open(LOG_FILE) as logfile:
            lines_start = sum(1 for line in logfile)

    result_path = backuper.backup()

    if uploader:
        uploader.upload(result_path)

    if cleaner:
        cleaner.clean(path.dirname(result_path))


    if not mail_recipients:
        return

    with open(LOG_FILE) as log_file:
        lines = [l for l in log_file]
        message += lines[lines_start:]
        send_mail(mail_recipients, message)


def main():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.DEBUG,
        format='[%(asctime)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    _log = logging.getLogger(LOGGER_NAME)
    handler = logging.StreamHandler()
    _log.addHandler(handler)

    worker(
        Backuper('dortmund', '/var/lib/postgresql/data/backup'),
        UploaderScp('/home/odoo/backups', 'odoo', 'superfly.maxcrc.de', 6666, "dortmund.dump")
    )

    worker(
        Backuper('duisburg','/var/lib/postgresql/data/backup'),
        UploaderScp('/home/odoo/backups', 'odoo', 'superfly.maxcrc.de', 6666, "duisburg.dump")
    )


if __name__ == '__main__':
    main()
