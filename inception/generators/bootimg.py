from .generator import Generator
import os, tempfile
class BootImgGenerator(Generator):
    def __init__(self, mkbootBin):
        super(BootImgGenerator, self).__init__()
        self.bin = mkbootBin
        self.base = None
        self.ramdiskaddr = None
        self.pagesize = 2048
        self.kernel = None
        self.ramdisk = None
        self.ramdisk_offset = None
        self.dt = None
        self.second_offset = None
        self.kernelCmdLine = None
        self.tags_offset = None
        self.secondsize = 0
        self.devicetreesize = 0
        self.signature = None
        self.second = None
        self.kernel_offset = None

        self.additionalArgsStr = ""

        self.argsMap = {
            "kernel": self.getKernel,
            "ramdisk": self.getRamdisk,
            "second": self.getSecondBootLoader,
            "cmdline": self.getKernelCmdLine,
            "base": self.getBaseAddr,
            "pagesize": self.getPageSize,
            "dt": self.getDeviceTree,
            "kernel_offset": self.getKernelOffset,
            "second_offset": self.getSecondOffset,
            "tags_offset": self.getTagsOffset,
            "ramdisk_offset": self.getRamdiskOffset,
            "ramdiskaddr": self.getRamdiskAddr,
            "signature": self.getSignature
        }


    def setSecondBootLoader(self, second):
        self.second = second

    def getSecondBootLoader(self):
        return self.second

    def setRamdisk(self, ramdisk):
        self.ramdisk = ramdisk

    def getRamdisk(self):
        return self.ramdisk

    def setDeviceTreeSize(self, size):
        self.devicetreesize = size

    def getDeviceTreeSize(self):
        return self.devicetreesize

    def setSecondSize(self, size):
        self.secondsize = size

    def getSecondSize(self):
        return self.secondsize

    def setTagsOffset(self, tagsOffset):
        self.tags_offset = tagsOffset

    def getTagsOffset(self):
        return self.tags_offset

    def setSecondOffset(self, second_offset):
        self.second_offset = second_offset

    def getSecondOffset(self):
        return self.second_offset

    def setKernelCmdLine(self, cmdline):
        self.kernelCmdLine = cmdline

    def getKernelCmdLine(self, quote = True):
        return self.kernelCmdLine
        # if self.kernelCmdLine:
        #     return "\"%s\"" % self.kernelCmdLine if quote else self.kernelCmdLine
        # return None

    def getKernelOffset(self):
        return self.kernel_offset

    def setKernelOffset(self, offset):
        self.kernel_offset = offset

    def setDeviceTree(self, dt):
        self.dt = dt

    def getDeviceTree(self):
        return self.dt

    def setRamdiskAddr(self, addr):
        self.ramdiskaddr = addr

    def getRamdiskAddr(self):
        return self.ramdiskaddr

    def setKernel(self, kernel):
        self.kernel = kernel

    def getKernel(self):
        return self.kernel

    def setBaseAddr(self, addr):
        self.base = addr

    def getBaseAddr(self):
        return self.base

    def setPageSize(self, pagesize):
        if pagesize is not None:
            self.pagesize = int(pagesize)

    def getPageSize(self):
        return self.pagesize

    def setSignature(self, signature):
        self.signature = signature

    def getSignature(self):
        return self.signature

    def setRamdiskOffset(self, offset):
        self.ramdisk_offset = offset

    def getRamdiskOffset(self):
        return self.ramdisk_offset

    def createArgs(self):
        args = ()
        for arg, getter in self.argsMap.items():
            val = getter()
            if val:
                args += ("--%s" % arg, str(val))
        return args



    def generate(self, out):
        ramdisk = self.getRamdisk()
        if os.path.isdir(ramdisk):
            self.d("Ramdisk is a dir, generating gzip")
            #files = self.execCmd("find", ".")
            fileList = tempfile.NamedTemporaryFile()
            fCpio = tempfile.TemporaryFile()
            ramdisk = self.getWorkDir() + "/ramdisk.cpio.gz"
            fRamdisk = open(ramdisk, "w+b")
            self.execCmd("find", ".", stdout = fileList, cwd = self.ramdisk)

            fileList.seek(0)
            self.execCmd("cpio", "-o", "-H", "newc", stdout = fCpio, stdin = fileList, cwd = self.ramdisk)
            fCpio.seek(0)
            self.execCmd("gzip", stdin = fCpio, stdout = fRamdisk, cwd = self.ramdisk)
            self.setRamdisk(ramdisk)

            fileList.close()
            fCpio.close()
            fRamdisk.close()

        args = self.createArgs()
        cmd = (self.bin,) + args + ("--output", out)
        #cmd = self.bin + " " + self.createArgs()  + " --output " + out
        self.execCmd(*cmd)
