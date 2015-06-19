from .maker import Maker
from inception.generators.bootimg import BootImgGenerator
import os
import shutil

class ImageMaker(Maker):

    def __init__(self, config, key, imageName):
        super(ImageMaker, self).__init__(config, key)
        self.imageName = imageName

    def make(self, workDir, outDir):
        bootConfigProp = self.getMakeProperty("img")
        bootConfig = bootConfigProp.getValue()

        if type(bootConfig) is str: #path to packed image
            shutil.copy(bootConfigProp.resolveAsRelativePath(), os.path.join(outDir, self.imageName))
            return

        key, mkbootbin = self.getHostBinary("mkbootimg")
        assert mkbootbin, "%s is not set" % key
        gen = BootImgGenerator(mkbootbin)
        gen.setWorkDir(workDir)

        ramdisk = self.getMakeProperty("img.ramdisk_dir").resolveAsRelativePath()
        if ramdisk is None:
            ramdisk = self.getMakeProperty("img.ramdisk").resolveAsRelativePath()

        kernel = self.getMakeProperty("img.kernel").resolveAsRelativePath()

        second = bootConfig["second"] if "second" in bootConfig else None
        cmdline = bootConfig["cmdline"] if "cmdline" in bootConfig else None
        base = bootConfig["base"] if "base" in bootConfig else None
        pagesize = bootConfig["pagesize"] if "pagesize" in bootConfig else None
        ramdisk_offset = bootConfig["ramdisk_offset"] if "ramdisk_offset" in bootConfig\
            else None
        ramdiskaddr = bootConfig["ramdiskaddr"] if "ramdiskaddr" in bootConfig else None
        devicetree = self.getMakeProperty("img.dt").resolveAsRelativePath()
        signature = bootConfig["signature"] if "signature" in bootConfig else None

        gen.setKernel(kernel)
        gen.setRamdisk(ramdisk)
        gen.setKernelCmdLine(cmdline)
        gen.setSecondBootLoader(second)
        gen.setPageSize(pagesize)
        gen.setBaseAddr(base)
        gen.setRamdiskOffset(ramdisk_offset)
        gen.setDeviceTree(devicetree)
        gen.setSignature(signature)
        gen.setRamdiskAddr(ramdiskaddr)

        out = os.path.join(outDir, self.imageName)
        gen.generate(out)

        return out