from .generator import Generator, GenerationFailedException
from exceptions import Ext4FSGenerationFailedException
from droidtools import ext4fs_utils
class Ext4FSGenerator(Generator):
    def __init__(self, ext4bin = None):
        super(Ext4FSGenerator, self).__init__()
        self.bin = ext4bin
        self.size = 0
        self.mountPoint = None
        self.sparsed = True

    def setSize(self, size):
        try:
            self.size = int(size)
        except ValueError:
            raise Ext4FSGenerationFailedException("Invalid Ext4 fs size")

    def setMountPoint(self, mountPoint):
        self.mountPoint = mountPoint

    def setSparsed(self, sparsed):
        self.sparsed = True if sparsed else False

    def generate(self, src, out):
        if self.size <= 0:
            raise Ext4FSGenerationFailedException("Ext4 fs size cannot be %s" % self.size)

        ext4fs_utils.make_ext4fs(out, src,
                                 self.size,
                                 self.mountPoint,
                                 mode=ext4fs_utils.MODE_SPARSED if self.sparsed else ext4fs_utils.MODE_NORMAL)

        return True