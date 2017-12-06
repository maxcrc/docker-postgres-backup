class UploaderSshFs(UploaderFuse):
    def __init__(self, src, dest, mount_point=None):
        super(UploaderSshFs,self).__init__(src, dest)
        self._mount_point = mount_point if mount_point else path.expanduser('~/backup-mnt-point')

    def upload(self):
        _log.info("Mounting the {} folder".format(self._dest))
        try:
            name_host, file_path = self._dest.split(':')
            filename = path.basename(self._src)
            dest = ':'.join([name_host, file_path])

            subprocess.call(['fusermount', '-u', '-z', self._mount_point])

            cmd = 'sshfs {} {} -o IdentityFile={}'.format(dest, self._mount_point, path.expanduser('~/.ssh/id_rsa'))
            c, _, __ = run_process(cmd.split(' '))

            if c != 0:
                raise RuntimeError('Can\'t mount remote FS')

            shutil.copy2(self._src, path.join(self._mount_point, filename))
        except Exception as e:
            _log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            run_process(['fusermount', '-u', '-z', self._mount_point])
