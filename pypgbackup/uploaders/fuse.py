class UploaderFuse:
    def __init__(self, src, dest):
        self._src = src
        self._dest = dest
        super(UploaderFuse, self).__init__(src, dest)

    def upload(self):
        _log.info("Mounting the {} folder".format(self._dest))
        try:
            subprocess.call(['fusermount', '-u', '-z', self._dest])
            subprocess.call(['mount', self._dest])
            shutil.copy2(self._src, self._dest)
            subprocess.call(['fusermount', '-u', self._dest])
        except Exception as e:
            _log.warning('Unable to copy file to remote location. Exception: {}'.format(e))
            raise
        finally:
            subprocess.call(['fusermount', '-u', '-z', self._dest])
