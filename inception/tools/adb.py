from .execwrapper import ExecWrapper
import os
class Adb(ExecWrapper):

    def __init__(self, bin):
        super(Adb, self).__init__(bin)
        self.busybox = False

    def _setAction(self, action):
        self.clearArgs()
        self.addPreArg(action)

    def setBusyBoxCmds(self, busybox):
        self.busybox = busybox

    def push(self, src, dest):
        self._setAction("push")
        self.addPostArg(src)
        self.addPostArg(dest)

        return self.run()

    def pull(self, src, dest, requireSu = False):

        if requireSu:
            tmpDir = "/sdcard/inceptiontmp"
            self.mkdir(tmpDir)
            self.cmd("cp", "-r", src, tmpDir, su = True)
            src = tmpDir + "/" + os.path.basename(src)
        self._setAction("pull")
        self.addPostArg(src)
        self.addPostArg(dest)

        return self.run() and self.rmdir(tmpDir)

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
        self._setAction("shell")
        if self.busybox:
            cmd = ("busybox",) + cmd
        if "su" in kwargs and kwargs["su"] is True:
            self.addPreArg("su -c")

        cmdFlat = " ".join(cmd)
        self.addPostArg("\"%s\"" % cmdFlat)

        return self.run()
