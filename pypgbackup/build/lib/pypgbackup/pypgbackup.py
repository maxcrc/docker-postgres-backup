import logging
from os import path
from utils import send_mail, setup_logging
from uploaders import UploaderFuse, UploaderScp, UploaderSshFs
from backuper import Backuper
from filedeleter import filedeleter
import configparser

def worker(backuper, configuration, uploader=None):
    lines_start = 0
    message = ""
    mail_recipients = configuration["Mail"].get("Recipients", None)
    delete_files = configuration["FileDeleter"].getbool("DeleteFiles", False)
    deleter_expr = configuration["FileDeleter"].get("Expr", None)
    
    if mail_recipients:
        with open(LOG_FILE) as logfile:
            lines_start = sum(1 for line in logfile)

    result_path = backuper.backup()

    if uploader:
        uploader.upload(result_path)

    if delete_files:
        filedeleter.delete(deleter_expr, path.dirname(result_path), False)

    if not mail_recipients:
        return

    with open(LOG_FILE) as log_file:
        lines = [l for l in log_file]
        message += lines[lines_start:]
        send_mail(mail_recipients, message)

def main():
    cnf = configparser.ConfigParser()
    cnf.read_file("./config.ini")
    gencnf = cnf["General"]
    setup_logging(gencnf["Log"]);

    dbnames = [ x for x in cnf.sections() if x.startswith("db-")]
    
    for db in dbnames:
        uploader_name = cnf[db].get("Uploader")
        uploader = getattr(globals(), uploader_name)
        uploader_args = cnf[db].get("UploaderArgs").split(',')
        backup_destination_folder = cnf[db].get("BackupDestenationFolder", '/var/lib/postgresql/data/backup')
        
        worker(
            Backuper(db.remove('db-'), backup_destination_folder),
            cnf,
            uploader(*uploader_args)
        )

if __name__ == '__main__':    
    main()
