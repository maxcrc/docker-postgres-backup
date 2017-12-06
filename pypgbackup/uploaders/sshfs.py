from os import path
import shutil
from subprocess import Popen, PIPE, call
from .fuse import UploaderFuse
from ..utils import log

class UploaderSshFs(UploaderFuse):
    def __init__(self, src, dest, mount_point=None):
        super(UploaderSshFs,self).__init__(src, dest)
        self._mount_point = mount_point if mount_point else path.expanduser('~/backup-mnt-point')

    def _run_process(self, args):
        log.debug('Running command: \'{}\''.format(' '.join(args)))
        process = Popen(args, stdout=PIPE)
        (output, err) = process.communicate()
        return process.wait(), output, err

    def upload(self):
        log.info("Mounting the {} folder".format(self._dest))
        try:
            name_host, file_path = self._dest.split(':')
            filename = path.basename(self._src)
            dest = ':'.join([name_host, file_path])

            call(['fusermount', '-u', '-z', self._mount_point])

            cmd = 'sshfs {} {} -o IdentityFile={}'.format(dest, self._mount_point, path.expanduser('~/.ssh/id_rsa'))
            c, _, __ = self._run_process(cmd.split(' '))

            if c != 0:
                raise RuntimeError('Can\'t mount remote FS')

            shutil.copy2(self._src, path.join(self._mount_point, filename))
        except Exception as e:
            log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            self._run_process(['fusermount', '-u', '-z', self._mount_point])
