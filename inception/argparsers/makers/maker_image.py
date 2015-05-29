from .maker import Maker
from inception.generators.bootimg import BootImgGenerator
import os
import shutil

class ImageMaker(Maker):

    def __init__(self, config, key, imageName):
        super(ImageMaker, self).__init__(config, key)
        self.imageName = imageName

    def make(self, workDir, outDir):
        bootConfigProp = self.getMakeConfigProperty("img")
        bootConfig = bootConfigProp.getValue()

        if type(bootConfig) is str: #path to packed image
            shutil.copy(bootConfigProp.resolveAsRelativePath(), os.path.join(outDir, self.imageName))
            return

        mkbootprop = self.getCommonConfigProperty("tools.mkbootimg.bin")
        assert mkbootprop.getValue(), "tools.mkbootimg.bin is not set"
        mkbootbin = mkbootprop.getConfig().resolveRelativePath(mkbootprop.getValue())
        gen = BootImgGenerator(mkbootbin)
        gen.setWorkDir(workDir)
        gen.setOutDir(outDir)


        ramdisk = self.getMakeConfigProperty("img.ramdisk_dir").resolveAsRelativePath()
        if ramdisk is None:
            ramdisk = self.getMakeConfigProperty("img.ramdisk").resolveAsRelativePath()

        kernel = self.getMakeConfigProperty("img.kernel").resolveAsRelativePath()

        second = bootConfig["second"] if "second" in bootConfig else None
        cmdline = bootConfig["cmdline"] if "cmdline" in bootConfig else None
        base = bootConfig["base"] if "base" in bootConfig else None
        pagesize = bootConfig["pagesize"] if "pagesize" in bootConfig else None
        ramdisk_offset = bootConfig["ramdisk_offset"] if "ramdisk_offset" in bootConfig\
            else None
        ramdiskaddr = bootConfig["ramdiskaddr"] if "ramdiskaddr" in bootConfig else None
        devicetree = self.getMakeConfigProperty("img.dt").resolveAsRelativePath()
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

        gen.generate(os.path.join(outDir, self.imageName))