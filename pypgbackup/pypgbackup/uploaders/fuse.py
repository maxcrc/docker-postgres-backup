import subprocess
import shutil
from utils import log

class UploaderFuse:
    def __init__(self, dest):
        self._dest = dest
      
    def upload(self, after_copy=None):
        log.info("Mounting the {} folder".format(self._dest))
        try:
            subprocess.call(['fusermount', '-u', '-z', self._dest])
            subprocess.call(['mount', self._dest])
            shutil.copy2(self._src, self._dest)

            if callable(after_copy):
                after_copy(self)
            
            subprocess.call(['fusermount', '-u', self._dest])
        except Exception as e:
            log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            subprocess.call(['fusermount', '-u', '-z', self._dest])
