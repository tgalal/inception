from inception.argparsers.makers.maker_image import ImageMaker
from inception.constants import InceptionConstants
from inception.tools import imgtools
from dumpkey import dumppublickey
import os
import logging
import shutil
logger = logging.getLogger(__name__)
class RecoveryImageMaker(ImageMaker):
    PATH_KEYS = "res/keys"
    def __init__(self, config):
        super(RecoveryImageMaker, self).__init__(config, "recovery", InceptionConstants.OUT_NAME_RECOVERY)

    def make(self, workDir, outDir):
        if self.getMakeProperty("inject_keys", True):
            keysName = self.config.get("update.keys", None)
            if not keysName:
                raise ValueError("recovery.inject_keys is set to true, but update.keys is not set")
            elif keysName == "test":
                if not self.config.get("update.restore_stock_recovery"):
                    logger.warning("\n========================\n\nWARNING: You requested inception to inject 'test' keys inside the recovery image. "
                                   "It's advised to either set update.restore_stock_recovery=true or use your own keys, "
                                   "otherwise anyone can install their own update packages through the modified recovery.\n\n========================")
                else:
                    logger.warning("\n========================\n\nWARNING: You requested inception to inject 'test' keys inside the recovery image. "
                                   "It's advised to use your own keys, "
                                   "otherwise anyone can install their own update packages through the modified recovery.\n\n========================")

            signingKeys = self.getConfig().getKeyConfig(keysName)
            assert signingKeys, "update.keys is '%s' but __config__.host.keys.%s is not set" % (keysName, keysName)
            pubPath = signingKeys["public"]

            keysVal = dumppublickey.print_rsa(pubPath)

            recoveryImg = self.getMakeProperty("img")

            if type(recoveryImg.getValue()) is str:
                _, unpacker = self.getHostBinary("unpackbootimg")
                with self.newTmpWorkDir() as recoveryExtractDir:
                    bootImgGenerator = imgtools.unpackimg(unpacker, recoveryImg.resolveAsRelativePath(), recoveryExtractDir)

                    if self.injectKey(os.path.join(bootImgGenerator.getRamdisk(), self.__class__.PATH_KEYS), keysVal):
                        logger.debug("injected key in %s" % self.__class__.PATH_KEYS)
                        imgType = "recovery"
                        self.setValue("recovery.img", {})
                        self.setValue("%s.img.cmdline" % imgType, bootImgGenerator.getKernelCmdLine(quote=False))
                        self.setValue("%s.img.base" % imgType, bootImgGenerator.getBaseAddr())
                        self.setValue("%s.img.ramdisk_offset" % imgType, bootImgGenerator.getRamdiskOffset())
                        self.setValue("%s.img.second_offset" % imgType, bootImgGenerator.getSecondOffset())
                        self.setValue("%s.img.tags_offset" % imgType, bootImgGenerator.getTagsOffset())
                        self.setValue("%s.img.pagesize" % imgType, bootImgGenerator.getPageSize())
                        self.setValue("%s.img.second_size" % imgType, bootImgGenerator.getSecondSize())
                        self.setValue("%s.img.dt_size" % imgType, bootImgGenerator.getDeviceTreeSize())
                        self.setValue("%s.img.kernel" % imgType, bootImgGenerator.getKernel())
                        self.setValue("%s.img.ramdisk" % imgType, bootImgGenerator.getRamdisk())
                        self.setValue("%s.img.dt" % imgType, bootImgGenerator.getDeviceTree())
                        result = super(RecoveryImageMaker, self).make(workDir, outDir)
                        self.setValue("recovery.img", recoveryImg.resolveAsRelativePath())
                        return result
                    else:
                        logger.warning("key already exists in %s, not injecting" % self.__class__.PATH_KEYS)
            else:
                with self.newTmpWorkDir() as recoveryRamDiskDir:
                    ramDiskPath = self.getMakeProperty("img.ramdisk").resolveAsRelativePath()
                    if not ramDiskPath or not os.path.exists(ramDiskPath):
                        raise ValueError("Invalid valid for recovery.img.ramdisk or path does not exist: %s" % ramDiskPath)

                    ramdiskTmpDir = os.path.join(recoveryRamDiskDir, "ramdisk")
                    shutil.copytree(ramDiskPath, ramdiskTmpDir, symlinks=True)
                    if self.injectKey(os.path.join(ramdiskTmpDir, self.__class__.PATH_KEYS), keysVal):
                        logger.debug("injected key in %s" % self.__class__.PATH_KEYS)
                        self.setValue("recovery.img.ramdisk", ramdiskTmpDir)
                        result = super(RecoveryImageMaker, self).make(workDir, outDir)
                        self.setValue("recovery.img.ramdisk", ramDiskPath)
                        return result
                    else:
                        logger.warning("key already exists in %s, not injecting" % self.__class__.PATH_KEYS)

        return super(RecoveryImageMaker, self).make(workDir, outDir)

    def injectKey(self, keysPath, keyData):
        with open(keysPath, 'r+') as keyfile:
            allKeys = []
            for key in keyfile.readlines():
                key = key.strip()
                key = key[:-1] if key.endswith(",") else key
                if keyData == key:
                    return False
                allKeys.append(key.strip())

            allKeys.append(keyData)
            keyfile.seek(0)
            keyfile.write(",\n".join(allKeys))

        return True
