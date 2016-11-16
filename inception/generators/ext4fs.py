from .generator import Generator, GenerationFailedException
from exceptions import Ext4FSGenerationFailedException
from ..constants import InceptionConstants
import time, sys
class Ext4FSGenerator(Generator):
    def __init__(self, ext4bin):
        super(Ext4FSGenerator, self).__init__()
        self.bin = ext4bin
        self.size = 0
        self.mountPoint = None
        self.sparsed = True

    def setSize(self, size):
        self.size = size

    def setMountPoint(self, mountPoint):
        self.mountPoint = mountPoint

    def setSparsed(self, sparsed):
        self.sparsed = True if sparsed else False

    def generateArgs(self, src, out):
        cmd = ("-l", str(self.size))
        if self.sparsed:
            cmd += ("-s",)
        if self.mountPoint is not None:
            cmd += ("-a", self.mountPoint)

        cmd += (out, src)

        return cmd

    def generate(self, src, out, adbBinPath = None):
        if self.size <= 0:
            raise Ext4FSGenerationFailedException("Ext4 fs size cannot be %s" % self.size)
        if not self.bin.startswith("device://"):
            args = self.generateArgs(src, out)
            cmd = (self.bin,) + args
            self.execCmd(*cmd)
        else:
            if not adbBinPath:
                print "Adb bin not specified"
                sys.exit(1)
            remoteBin = self.bin.split("device://")[1]
            remoteSrc = "/tmp/cache"
            remoteOut = "/tmp/cache.img"
            remoteArgs = self.generateArgs(remoteSrc, remoteOut)
            remoteCmd = (remoteBin,) + remoteArgs
            adb = self.getAdb(adbBinPath)
            adb.cmd("mkdir", remoteSrc)
            adb.push(src, remoteSrc)
            adb.cmd(*remoteCmd)
            adb.pull(remoteOut, out)

        return True