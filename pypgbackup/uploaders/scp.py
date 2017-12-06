from os import path
import paramiko
from .fuse import UploaderFuse
from ..utils import log


class UploaderScp(UploaderFuse):
    def __init__(self, src, dest, username, hostname, port=22, dest_file_name=None):
        super(UploaderScp,self).__init__(src, dest)
        self._username = username
        self._hostname = hostname
        self._port = port
        self._dest_file_name = dest_file_name
        self._client = None

    def _connect(self):
        key_filename = path.expanduser(path.join('~', '.ssh', 'id_rsa'))

        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(self._hostname, port=self._port, username=self._username, key_filename=key_filename)

        log.info('Connecting to \'{}:{}\'. As user: \'{}\'. Using key from \'{}\''.format(self._hostname, self._port, self._username,
                                                                                           key_filename))

    def _disconnect(self):
        if self._client:
            self._client.close()

    def upload(self):
        try:
            log.info('Uploading backup on {}:{}'.format(self._hostname, self._port))
            if self._dest_file_name:
                dest = path.join(path.dirname(self._dest), self._dest_file_name)

            self._client.open_sftp().put(self._src, dest)
        except Exception as e:
            log.error('Upload failed. Exception: {}'.format(e))
        finally:
            self._disconnect();
