import logging
import calendar
from datetime import datetime
from dateutils import relativedelta
from os import path, remove, listdir
import smtplib

LOGGER_NAME = "Backup"
LOG_FILE = "backup.log"

log = logging.getLogger(LOGGER_NAME)
logging.getLogger("paramiko").setLevel(logging.WARNING)


def clean(backup_folder):
    files = [path.join(backup_folder, f) for f in listdir(backup_folder) if
             path.isfile(path.join(backup_folder, f)) and f.lower().endswith('.backup')]

    def _delete_file(f):
        mtime = datetime.fromtimestamp(path.getmtime(f))
        last_day = calendar.monthrange(mtime.year, mtime.month)[1]
        if mtime < datetime.now() - relativedelta(months=2) and mtime.day != last_day and mtime.day != 1:
            return True
        return False

    log.info("Removing backups that are older than 60 days and which was not created and start/end of month")

    map(remove, filter(_delete_file, files))


def send_mail(mail_recepients, message):
    server = smtplib.SMTP('smtp.gmail.com:587', timeout=60)
    server.ehlo()
    server.starttls()
    server.login('pp.foss.pp@gmail.com', '123qwerty123')

    for recipient in mail_recepients:
        server.sendmail('pp.foss.pp@gmail.com', recipient, ''.join(message))

    server.quit()
