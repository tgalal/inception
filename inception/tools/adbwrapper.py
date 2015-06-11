from .execwrapper import ExecWrapper
import os
import sys
import usb1
import logging
from adb.adb_commands import AdbCommands, M2CryptoSigner
from Crypto.PublicKey import RSA

from inception.constants import InceptionConstants

logger = logging.getLogger(__name__)

def catchUsbBusy(fn):
    def wrapped(*args):
        try:
            return fn(*args)
        except usb1.USBErrorBusy as e:
            logger.error("Could not claim USB device, got LIBUSB_ERROR_BUSY.\nIf you have a running adb server, you'll need to stop it by running 'adb kill-server' and then try again")
            sys.exit(1)

    return wrapped

class Adb(ExecWrapper):
    def __init__(self):
        super(Adb, self).__init__(None)
        self.busybox = False
        self.connection = None
        if not os.path.exists(InceptionConstants.PATH_RSA_KEY):
            logger.warning("%s does not exist, going to generate RSA keys" % InceptionConstants.PATH_RSA_KEY)
            private = RSA.generate(1024)
            public  = private.publickey()
            with open(InceptionConstants.PATH_RSA_KEY, 'w') as privateKeyFile:
                privateKeyFile.write(private.exportKey())

            with open(InceptionConstants.PATH_RSA_KEY + ".pub", "w") as publicKeyFile:
                publicKeyFile.write(public.exportKey())

        self.rsaKeys =  [M2CryptoSigner(os.path.expanduser(InceptionConstants.PATH_RSA_KEY))]

    def getConnection(self):
        if self.connection is None:
            self.connection = AdbCommands.ConnectDevice(rsa_keys = self.rsaKeys)
        return self.connection

    def setBusyBoxCmds(self, busybox):
        self.busybox = busybox

    @catchUsbBusy
    def push(self, src, dest):
        return self.getConnection().Push(src, dest)

    @catchUsbBusy
    def pull(self, src, dest, requireSu = False):
        conn = self.getConnection()
        conn.Pull(src, dest)

    def rmdir(self, dirname):
        return self.cmd("rm", "-r", dirname)

    def mkdir(self, dirname):
        return self.cmd("mkdir", dirname)

    @catchUsbBusy
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

    @catchUsbBusy
    def run(self, preview = False):
        cmd = self.createArgs()
        return self.getConnection().Shell( '"' + " ".join(cmd) + '"')
