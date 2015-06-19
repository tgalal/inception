from .execwrapper import ExecWrapper
import os
import sys
import usb1
import logging
from adb.adb_commands import AdbCommands, M2CryptoSigner
from adb.usb_exceptions import AdbCommandFailureException
from Crypto.PublicKey import RSA
import time

from inception.constants import InceptionConstants

logger = logging.getLogger(__name__)

def catchUsbBusy(fn):
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except usb1.USBErrorBusy as e:
            logger.error("Could not claim USB device, got LIBUSB_ERROR_BUSY.\nIf you have a running adb server, you'll need to stop it by running 'adb kill-server' and then try again")
            sys.exit(1)

    return wrapped

class Adb(ExecWrapper):
    def __init__(self):
        super(Adb, self).__init__(None)
        self.busybox = False

        if not os.path.exists(InceptionConstants.PATH_RSA_KEY):
            logger.warning("%s does not exist, going to generate RSA keys" % InceptionConstants.PATH_RSA_KEY)
            if not os.path.exists(os.path.dirname(InceptionConstants.PATH_RSA_KEY)):
                os.makedirs(os.path.dirname(InceptionConstants.PATH_RSA_KEY))
            private = RSA.generate(1024)
            public  = private.publickey()
            with open(InceptionConstants.PATH_RSA_KEY, 'w') as privateKeyFile:
                privateKeyFile.write(private.exportKey())

            with open(InceptionConstants.PATH_RSA_KEY + ".pub", "w") as publicKeyFile:
                publicKeyFile.write(public.exportKey())

        self.rsaKeys =  [M2CryptoSigner(InceptionConstants.PATH_RSA_KEY)]

    def getConnection(self):
        #maintaining just for some reason is not stable
        return AdbCommands.ConnectDevice(rsa_keys = self.rsaKeys)

    def setBusyBoxCmds(self, busybox):
        self.busybox = busybox

    @catchUsbBusy
    def shell(self, cmd):
        return self.getConnection().Shell(cmd)

    @catchUsbBusy
    def push(self, src, dest):
        return self.getConnection().Push(src, dest)

    @catchUsbBusy
    def pull(self, src, dest):
        conn = self.getConnection()
        try:
            conn.Pull(src, dest)
        except AdbCommandFailureException:
            self.superPull(src, dest)

    @catchUsbBusy
    def superPull(self, src, dest, fallback = False):
        try:
            conn = self.getConnection()
            tmpDir = "/sdcard/inception_tmp"
            conn.Shell("rm -r %s" % tmpDir)
            conn.Shell("mkdir %s" % tmpDir)
            conn.Shell("su -c cp -r %s %s" % (src, tmpDir))
            newSrc = os.path.join(tmpDir, os.path.basename(src))
            conn.Pull(newSrc, dest)
        except:
            if fallback:
                self.getConnection().Pull(src, dest)
            else:
                raise
