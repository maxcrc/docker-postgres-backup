#!/usr/bin/env python2
from os import path, listdir, remove, makedirs
import logging
import subprocess
import shutil
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import smtplib
import paramiko
from subprocess import Popen, PIPE
import json
from os import path

LOGGER_NAME = "Backup"
LOG_FILE = "backup.log"
_log = logging.getLogger(LOGGER_NAME)

logging.getLogger("paramiko").setLevel(logging.WARNING)

def run_process(args):
    _log.debug('Running command: \'{}\''.format(' '.join(args)))
    process = Popen(args, stdout=PIPE)
    (output, err) = process.communicate()
    return process.wait(), output, err


def upload_backup_scp(src, dest, username, hostname, port=22, dest_file_name=None):
    ssh_client = None
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        key_filename = path.expanduser(path.join('~', '.ssh', 'id_rsa'))
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _log.info('Connecting to \'{}:{}\'. As user: \'{}\'. Using key from \'{}\''.format(hostname, port, username,
                                                                                           key_filename))
        ssh_client.connect(hostname, port=port, username=username, key_filename=key_filename)

        _log.info('Uploading backup on {}:{}'.format(hostname, port))

        if dest_file_name:
            dest = path.join(path.dirname(dest), dest_file_name)

        ssh_client.open_sftp().put(src, dest)
    except Exception as e:
        _log.error('Upload failed. Exception: {}'.format(e))
        return False
    else:
        return True
    finally:
        if ssh_client:
            ssh_client.close()

def upload_backup_sshfs(src, dest, mount_point=path.expanduser('~/backup-mnt-point')):
    _log.info("Mounting the {} folder".format(dest))
    try:
        name_host, file_path = dest.split(':')
        filename = path.basename(src)
        dest = ':'.join([name_host, file_path])

        subprocess.call(['fusermount', '-u', '-z', mount_point])

        cmd = 'sshfs {} {} -o IdentityFile={}'.format(dest, mount_point, path.expanduser('~/.ssh/id_rsa'))
        c, _, __ = run_process(cmd.split(' '))

        if c != 0:
            raise RuntimeError('Can\'t mount remote FS')

        shutil.copy2(src, path.join(mount_point, filename))
    except Exception as e:
        _log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
        raise
    finally:
        run_process(['fusermount', '-u', '-z', mount_point])


def upload_backup_fuse(src, dest):
    _log.info("Mounting the {} folder".format(dest))
    try:
        subprocess.call(['fusermount', '-u', '-z', dest])
        subprocess.call(['mount', dest])
        shutil.copy2(src, dest)
        subprocess.call(['fusermount', '-u', dest])
    except Exception as e:
        _log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
        raise
    finally:
        subprocess.call(['fusermount', '-u', '-z', dest])


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


def do_backup_simple(backup_folder, db_name):
    timeslot = datetime.now().strftime('%Y%m%d%H%M')
    backup_file = path.join(backup_folder, "{}-database-{}.backup".format(db_name, timeslot))

    _log.info("Running vacuum on the database.")
    subprocess.call(['/usr/bin/vacuumdb', db_name])
    _log.info("Running pg_dump on the database.")
    subprocess.call(['/usr/bin/pg_dump', '-Fc', '-b', db_name, '-f', backup_file])
    _log.info("Backup and Vacuum complete for database '{}'".format(db_name))

    return backup_file

def do_backup_docker(backup_folder, db_name, container='postgresql', db_username='postgres'):
    def get_container_folder():
        code, s_out, s_err = run_process(["docker", "inspect", '-f', '{{ json .Mounts }}', container])
        if code != 0:
            raise RuntimeError('Can\'t get mount source')

        mounts = json.loads(s_out)
        for mount in mounts:
            is_subpath = path.normpath(backup_folder).startswith(path.normpath(mount.get('Source')))
            subpath = path.relpath(backup_folder, mount.get('Source'))

            if is_subpath:
                _log.info("Backup and Vacuum complete for database '{}'".format(db_name))
                return path.join(mount.get('Destination'), subpath or '')

        return ''

    timeslot = datetime.now().strftime('%Y%m%d%H%M')
    file_name = "{}-database-{}.backup".format(db_name, timeslot)

    _log.info("Running vacuum on the database.")

    code, s_out, s_error =  run_process(['docker', 'exec', '-t', '-u', 'postgres', container, '/usr/bin/vacuumdb', db_name])
    if code != 0:
        raise RuntimeError('Can\'t vacuum the database.\nstdout:\n {}\nstderr: {}\n'.format(s_out, s_error))


    _log.info("Running pg_dump on the database.")

    container_folder = get_container_folder()

    if not container_folder:
        raise RuntimeError("Cannot find container directory to put the backup in.")

    args = ['docker', 'exec', '-t', container, 'pg_dump', '--no-owner', '-Fc', '-f', path.join(container_folder, file_name), '-b', db_name]

    if db_username:
        args.append('--username=' + db_username)


    code, s_out, s_error =  run_process(args)
    if code != 0:
        raise RuntimeError('Can\'t vacuum the database.\nstdout:\n {}\nstderr: {}\n'.format(s_out))

    backup_file = path.join(backup_folder, file_name)

    if not path.exists(backup_file):
        raise RuntimeError('Failed to create the backup. File {} does\'t exist'.format(backup_file))

    return backup_file

def send_mail(mail_recepients, message):
    server = smtplib.SMTP('smtp.gmail.com:587', timeout=60)
    server.ehlo()
    server.starttls()
    server.login('pp.foss.pp@gmail.com', '123qwerty123')

    for r in mail_recepients:
        server.sendmail('pp.foss.pp@gmail.com', r, ''.join(message))

    server.quit()

def do_backup(db_names, backup_folder, backuper, uploader=None, mail_recipients=None, do_clean=False):
    databases = db_names
    if isinstance(databases, str):
        databases = [db_names]

    if not path.exists(backup_folder):
        print("Base folder {} doesn't exists. Creating".format(path.dirname(backup_folder)))
        try:
            makedirs(backup_folder)
        except OSError as e:
            print('Can\'t create {}. Exception: {}'.format(backup_folder, e))
            exit(1)

    lines_start = 0
    message = ""
    if mail_recipients:
        with open(LOG_FILE) as f:
            lines_start = sum(1 for line in f)

    for db_name in databases:
        try:
            backup_func = backuper[0]
            backup_args = [backup_folder, db_name]
            backup_args.extend(backuper[1:])
            backup_path = backup_func(*backup_args)

            if uploader:
                uploader_func = uploader[0]
                dest_path = path.join(uploader[1], path.basename(backup_path))
                uploader_args = [backup_path, dest_path]
                uploader_args.extend(uploader[2:])
                uploader_func(*uploader_args)

            if do_clean:
                clean(backup_folder)

        except Exception as e:
            _log.error('Exception occured. Exception: {}'.format(e.message))
        finally:
            message = ["Subject:Odoo db backup finished\n\n", ]

    if mail_recipients:
        with open(LOG_FILE) as f:
            lines = [l for l in f]
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

    do_backup('dortmund',
             '/var/lib/postgresql/data/backup',
             (do_backup_docker,),
             (upload_backup_scp, '/home/odoo/backups', 'odoo', 'superfly.maxcrc.de', 6666, "dortmund.dump"),
    )

    do_backup('duisburg',
             '/var/lib/postgresql/data/backup',
             (do_backup_docker,),
             (upload_backup_scp, '/home/odoo/backups', 'odoo', 'superfly.maxcrc.de', 6666, "duisburg.dump"),
    )


if __name__ == '__main__':
    main()
