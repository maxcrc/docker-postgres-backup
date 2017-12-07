from os import path, getuid, mkdir
import getpass
import shutil
from subprocess import Popen, PIPE, call
from .fuse import UploaderFuse
from utils import log

class UploaderSshFs(UploaderFuse):
    def __init__(self,
                 dest=None,
                 host=None,
                 port=None,
                 user=None,
                 identity=None,
                 mount_point=None):
        
        super(UploaderSshFs,self).__init__(dest)
        self._user = user if user else getpass.getuser()
        self._host = host if host else 'localhost'
        self._port = port if port else 22
        self._identity = identity if identity else path.expanduser('~/.ssh/id_rsa')
        self._mount_point = mount_point if mount_point else path.expanduser('~/backup-mnt-point')

    def _run_process(self, args):
        log.debug('Running command: \'{}\''.format(' '.join(args)))
        process = Popen(args, stdout=PIPE)
        (output, err) = process.communicate()
        return process.wait(), output, err

    def upload(self, src, after_copy=None):
        log.info("Mounting the {} folder".format(self._dest))
        try:
            filename = path.basename(src)
            
            call(['fusermount', '-u', '-z', self._mount_point])

            if not path.isdir(self._mount_point):
                mkdir(self._mount_point)

            
            cmd = 'sshfs {} {}@{}:{} {} -o IdentityFile={},StrictHostKeyChecking=no'.format(
                "-p " + str(self._port),
                self._user,
                self._host,
                self._dest,
                self._mount_point,
                self._identity)
            
            print(cmd)
            c, _, __ = self._run_process(cmd.split(' '))

            if c != 0:
                raise RuntimeError('Can\'t mount remote FS')
            
            shutil.copy2(src, path.join(self._mount_point, filename))

            if callable(after_copy):
                after_copy(self)

        except Exception as e:
            log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            self._run_process(['fusermount', '-u', '-z', self._mount_point])
