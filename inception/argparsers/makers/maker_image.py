from .maker import Maker
from inception.generators.bootimg import BootImgGenerator
from inception.tools.bootsignature import BootSignature
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
            return os.path.join(outDir, self.imageName)

        key, mkbootbin = self.getHostBinary("mkbootimg")
        assert mkbootbin, "%s is not set" % key
        gen = BootImgGenerator(mkbootbin)
        gen.setWorkDir(workDir)

        ramdisk = self.getMakeProperty("img.ramdisk_dir").resolveAsRelativePath()
        if ramdisk is None:
            ramdisk = self.getMakeProperty("img.ramdisk").resolveAsRelativePath()

        kernel = self.getMakeProperty("img.kernel").resolveAsRelativePath()

        second = bootConfig["second"] if "second" in bootConfig else None
        secondOffset = bootConfig["second_offset"] if "second_offset" in bootConfig else None
        tagsOffset = bootConfig["tags_offset"] if "tags_offset" in bootConfig else None
        kernelOffset = bootConfig["kernel_offset"] if "kernel_offset" in bootConfig else None
        cmdline = bootConfig["cmdline"] if "cmdline" in bootConfig else None
        base = bootConfig["base"] if "base" in bootConfig else None
        pagesize = bootConfig["pagesize"] if "pagesize" in bootConfig else None
        ramdisk_offset = bootConfig["ramdisk_offset"] if "ramdisk_offset" in bootConfig\
            else None
        ramdiskaddr = bootConfig["ramdiskaddr"] if "ramdiskaddr" in bootConfig else None
        devicetree = self.getMakeProperty("img.dt").resolveAsRelativePath()
        signature = bootConfig["signature"] if "signature" in bootConfig else None

        with self.newTmpWorkDir() as imgWorkDir:
            ramdiskDir = os.path.join(imgWorkDir, "ramdisk")
            shutil.copytree(ramdisk, ramdiskDir, symlinks=True)
            gen.setKernel(kernel)
            gen.setRamdisk(ramdiskDir)
            gen.setKernelCmdLine(cmdline)
            gen.setSecondBootLoader(second)
            gen.setPageSize(pagesize)
            gen.setBaseAddr(base)
            gen.setRamdiskOffset(ramdisk_offset)
            gen.setDeviceTree(devicetree)
            gen.setSignature(signature)
            gen.setRamdiskAddr(ramdiskaddr)
            gen.setTagsOffset(tagsOffset)
            gen.setKernelOffset(kernelOffset)
            gen.setSecondOffset(secondOffset)

            keys_name = self.getMakeValue("keys")

            if keys_name:
                signingKeys = self.getConfig().getKeyConfig(keys_name)
                assert signingKeys, "No signing keys names %s" % keys_name
            else:
                signingKeys = None
            intermediateOut = os.path.join(workDir, "unsigned_%s.img" % self.imageName)
            out = os.path.join(outDir, self.imageName)
            if signingKeys is not None:
                gen.generate(intermediateOut)
                javaKey, javaPath = self.getHostBinary("java")
                bootsigKey, bootsigPath = self.getHostBinary("BootSignature")

                assert bootsigPath, "%s is not set" % bootsigKey

                assert os.path.exists(bootsigPath), "'%s' from %s does not exist" % (bootsigPath, bootsigKey)
                assert os.path.exists(javaPath), "'%s' from %s does not exist" % (javaPath, javaKey)

                bootsig = BootSignature(javaPath, bootsigPath)
                bootsig.sign("/" + self.imageName.split(".")[0], intermediateOut, signingKeys["private"], signingKeys["public"], out)
            else:
                gen.generate(out)



        return out
