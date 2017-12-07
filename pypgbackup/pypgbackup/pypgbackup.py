import logging
from os import path
from utils import send_mail, setup_logging
from uploaders.fuse import UploaderFuse
from uploaders.scp import UploaderScp
from uploaders.sshfs import UploaderSshFs
from backuper import Backuper
from filedeleter import filedeleter
import configparser

def worker(backuper, configuration, uploader=None):
    delete_files = configuration["FileDeleter"].get("DeleteFiles", False)
    deleter_expr = configuration["FileDeleter"].get("Expr", None)

    result_path = backuper.backup()

    if uploader:
        uploader.upload(result_path)

    #if delete_files:
    #    filedeleter.delete(deleter_expr, path.dirname(result_path), False)
    
def main():
    cnf = configparser.ConfigParser()
    cnf.read("./example.config.ini")
    gencnf = cnf["General"]
    setup_logging(gencnf["Log"]);

    dbnames = [ x for x in cnf.sections() if x.startswith("db-")]
    
    for db in dbnames:
        lines_start = 0
        message = ""
        uploader_name = cnf[db].get("Uploader")

        from pprint import pprint
        # pprint(dict(cnf[db]))

        
        uploader = globals().get(uploader_name)
        backup_destination_folder = cnf[db].get("BackupDestenationFolder", '/var/lib/postgresql/data/backup')
        mail_recipients = cnf["Mail"].get("Recipients", None)
        
        if mail_recipients:
            with open(gencnf["Log"]) as logfile:
                lines_start = sum(1 for line in logfile)

        uploader_args = {
            'dest' :             cnf[db].get('uploaderdestination'),
            'host' :             cnf[db].get('uploaderhost'),
            'port' :             cnf[db].get('uploaderport'),
            'user' :             cnf[db].get('uploaderuser'),
            'identity' :         cnf[db].get('uploaderkey'),
            'mount_point' :      cnf[db].get('uploadermountpoint')
        }

        pprint(uploader_args)
        
        worker(
            Backuper(db.replace('db-',''), backup_destination_folder, cnf[db]["DBHost"], cnf[db]["DBPort"], cnf[db]["DBUser"], cnf[db]["DBPassword"]),
            cnf,
            uploader(**uploader_args)
        )

        if not mail_recipients:
            return
        
        with open(gencnf["Log"]) as log_file:
            lines = [l for l in log_file]
            message += lines[lines_start:]
            send_mail(mail_recipients, message)

        
if __name__ == '__main__':    
    main()
