#!/usr/bin/env python3

from calendar import monthrange
from datetime import datetime, timedelta
from os import path, listdir, getcwd, remove
import logging
import argparse
import sys
from glob import glob


def _shoulddeletefile(filepath, expr):
    now = datetime.now()
    mtime = datetime.fromtimestamp(path.getmtime(filepath))
    monthend = monthrange(mtime.year, mtime.month)[1]

    todelete = eval(expr, {'__builtins__': {}, 'datetime': datetime, 'timedelta': timedelta }, {'now': now, 'mtime': mtime, 'monthend': monthend})

    logging.debug('expr: "{}" filepath: "{}", mtime: "{}", monthend: "{}", todelete: {}.'.format(expr, filepath, mtime, monthend, todelete))

    return todelete

def _removefiles(filestodelete, dryrun=False):
    for filepath in filestodelete:
        if not dryrun:
            remove(filepath)

def delete(expr, filePath, dryrun):
    files = [ path.join(filePath, x) for x in glob(filePath) ]
    _removefiles(
        [ x for x in files if path.isfile(x) and _shoulddeletefile(x, expr) ],
        dryrun
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete all files leaving based on the expression. glob patterns allowed')
    parser.add_argument('expr', help='python expression if it evaluates to True file will be deleted', default='False', required=True)
    parser.add_argument('path', nargs='?', help='path to delete files in', default=getcwd())
    parser.add_argument('-v', '--verbosity', help='output debugging information', action='count', default=False)
    parser.add_argument('-d', '--dryrun', help='do not delete anything just output debugging information', action='store_true', default=False)
    args = parser.parse_args()

    log_level = logging.CRITICAL

    if args.verbosity == 1:
        log_level = logging.INFO
    elif args.verbosity >= 2:
        log_level = logging.DEBUG

    if args.dryrun:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        stream=sys.stdout
    )

    if args.dryrun:
        logging.debug("Dry run won't delete anything")

    delete(args.expr, args.path, args.dryrun)
