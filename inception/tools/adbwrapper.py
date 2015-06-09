from .execwrapper import ExecWrapper
import os
from adb.adb_commands import AdbCommands, M2CryptoSigner
import stat
import sys
class Adb(ExecWrapper):
    def __init__(self):
        super(Adb, self).__init__(None)
        self.busybox = False
        self.connection = None
        self.rsaKeys =  [M2CryptoSigner(os.path.expanduser("~/.android/adbkey"))]

    def getConnection(self):
        if self.connection is None:
            self.connection = AdbCommands.ConnectDevice(rsa_keys = self.rsaKeys)
        return self.connection

    def setBusyBoxCmds(self, busybox):
        self.busybox = busybox

    def push(self, src, dest):
        return self.getConnection().Push(src, dest)

    def pull(self, src, dest, requireSu = False):
        conn = self.getConnection()
        conn.Pull(src, dest)

    def rmdir(self, dirname):
        return self.cmd("rm", "-r", dirname)

    def mkdir(self, dirname):
        return self.cmd("mkdir", dirname)

    def devices(self):
        self._setAction("devices")
        devices = {}
        result = self.run()
        result = result.rstrip().split('\n')[1:]
        for r in result:
            dissect = r.split('\t')
            devices[dissect[0]] = dissect[-1]
        return devices

    def cmd(self, *cmd, **kwargs):
        self.clearArgs()
        if self.busybox:
            cmd = ("busybox",) + cmd
        if "su" in kwargs and kwargs["su"] is True:
            self.addPreArg("su -c")

        cmdFlat = " ".join(cmd)
        self.addPostArg("\"%s\"" % cmdFlat)

        return self.run()


    def run(self, preview = False):
        cmd = self.createArgs()
        return self.getConnection().Shell( '"' + " ".join(cmd) + '"')
