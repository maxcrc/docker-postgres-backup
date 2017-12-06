import logging
from os import path
from utils import send_mail
from uploaders import UploaderFuse, UploaderScp, UploaderSshFs
from backuper import Backuper

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
