#!/usr/bin/env python3

from calendar import monthrange
from datetime import datetime, timedelta
from os import path, listdir, getcwd, remove
import logging
import argparse
import sys


def shoulddeletefile(filepath):
    mtime = datetime.fromtimestamp(path.getmtime(filepath))
    lastdayofmonth = monthrange(mtime.year, mtime.month)
    msgfmt = 'filepath: "{}", mtime: "{}", lastdayofmonth: "{}", todelete: {}'
    todelete = False
    
    if mtime.day != 1 and mtime.day != lastdayofmonth[1] and (datetime.now() - mtime) > timedelta(days=7):
        todelete = True

    logging.debug(msgfmt.format(filepath, mtime, lastdayofmonth[1], todelete))
        
    return todelete


def removefiles(filestodelete, dryrun=False):    
    for filepath in filestodelete:
        if not dryrun:
            remove(filepath)

            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete all files leaving only files created at the start/end of the month and which are not older than 7 days')
    parser.add_argument('path', nargs='?', help='path to delete files in', default=getcwd())
    parser.add_argument('-v', '--verbosity', help='output debugging information', action='count', default=False)
    parser.add_argument('-d', '--dryrun', help='do not delete anything just output debugging information', action='store_true', default=False)
    args = parser.parse_args()

    loglevel = logging.CRITICAL
    
    if args.verbosity == 1:
        loglevel = logging.INFO
    elif args.verbosity >= 2:
        loglevel = logging.DEBUG

    if args.dryrun:
        loglevel = logging.DEBUG
        
    logging.basicConfig(
        level=loglevel,
        format='%(message)s',
        stream=sys.stdout
    )

    if args.dryrun:
        logging.debug("Dry run won't delete anything")
    
    removefiles([ x for x in listdir(args.path) if path.isfile(x) and shoulddeletefile(x) ], args.dryrun)
    
