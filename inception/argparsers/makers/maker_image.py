from .maker import Maker
import os
import shutil
from droidtools.bootimg import BootImg
from inception.tools import imgtools

class ImageMaker(Maker):

    def __init__(self, config, key, imageName):
        super(ImageMaker, self).__init__(config, key)
        self.imageName = imageName

    def make(self, workDir, outDir):
        bootConfigProp = self.getMakeProperty("img")
        bootConfig = bootConfigProp.getValue()

        if type(bootConfig) is str: #path to packed image
            shutil.copy(bootConfigProp.resolveAsRelativePath(), os.path.join(outDir, self.imageName))
            return os.path.join(outDir, self.imageName)

        bootImg = BootImg()

        bootImg.ramdisk = self.getMakeProperty("img.ramdisk_dir").resolveAsRelativePath()
        if bootImg.ramdisk is None:
            bootImg.ramdisk = self.getMakeProperty("img.ramdisk").resolveAsRelativePath()

        bootImg.kernel = self.getMakeProperty("img.kernel").resolveAsRelativePath()

        bootImg.second = bootConfig["second"] if "second" in bootConfig else None
        bootImg.cmdline = bootConfig["cmdline"] if "cmdline" in bootConfig else None
        bootImg.base = bootConfig["base"] if "base" in bootConfig else None
        bootImg.page_size = bootConfig["pagesize"] if "pagesize" in bootConfig else None
        bootImg.ramdisk_offset = bootConfig["ramdisk_offset"] if "ramdisk_offset" in bootConfig\
            else None
        # ramdiskaddr = bootConfig["ramdiskaddr"] if "ramdiskaddr" in bootConfig else None
        bootImg.dt = self.getMakeProperty("img.dt").resolveAsRelativePath()
        bootImg.signature = bootConfig["signature"] if "signature" in bootConfig else None

        out = os.path.join(outDir, self.imageName)

        imgtools.packimg(bootImg, out)


        return out
