from inception.argparsers.makers.maker_image import ImageMaker
from inception.constants import InceptionConstants
from inception.tools import imgtools
from inception.argparsers.makers.submakers.submaker_busybox import BusyboxSubmaker
from inception.common.fstabtools import Fstab
from inception.common.configsyncer import ConfigSyncer
from dumpkey import dumppublickey
import sys
import os
import logging
import shutil
logger = logging.getLogger(__name__)
class RecoveryImageMaker(ImageMaker):
    PATH_KEYS = "res/keys"
    FSTABS = ["recovery.fstab", "twrp.fstab"]
    def __init__(self, config):
        super(RecoveryImageMaker, self).__init__(config, "recovery", InceptionConstants.OUT_NAME_RECOVERY)
        self.recoveryBootImgGen = None

    def make(self, workDir, outDir):
        recoveryImg = self.getMakeProperty("img")
        preprocessed = self.getMakeValue("preprocessed", False)

        with self.newTmpWorkDir() as recoveryExtractDir:
            with self.newTmpWorkDir() as recoveryRamdiskDir:
                workRamdiskDir = os.path.join(recoveryRamdiskDir, "ramdisk")
                if type(recoveryImg.getValue()) is str:
                    if preprocessed:
                        return super(RecoveryImageMaker, self).make(workDir, outDir)

                    unpackerName = self.getMakeValue("unpacker", "unpackbootimg")
                    assert unpackerName in ("unpackbootimg", "unmkbootimg")
                    _, unpacker = self.getHostBinary(unpackerName)
                    bootImgGenerator = imgtools.unpackimg(unpacker, recoveryImg.resolveAsRelativePath(),
                                                          recoveryExtractDir,
                                                          mode = imgtools.MODE_UNMKBOOTIMG if unpackerName == "unmkbootimg" else imgtools.MODE_UNPACKBOOTIMG)
                    shutil.copytree(os.path.join(recoveryExtractDir, bootImgGenerator.getRamdisk()), workRamdiskDir, symlinks=True)

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
                    self.setValue("%s.img.dt" % imgType, bootImgGenerator.getDeviceTree())
                    self.setValue("%s.img.kernel_offset" % imgType, bootImgGenerator.getKernelOffset())
                else:
                    shutil.copytree(self.getMakeProperty("img.ramdisk").resolveAsRelativePath(), workRamdiskDir, symlinks=True)


                self.setValue("recovery.img.ramdisk", workRamdiskDir)
                if not preprocessed:
                    if self.getMakeValue("inject_keys", True):
                        if not self.injectKeys(workRamdiskDir):
                            logger.warning("key already exists in %s, not injecting" % self.__class__.PATH_KEYS)
                        else:
                            logger.debug("injected key in %s" % self.__class__.PATH_KEYS)

                    self.injectBusyBox(workRamdiskDir)
                    self.readProps(workRamdiskDir)
                    self.overrideDmVerityHash(workRamdiskDir)


                    fstabPath = os.path.join(workRamdiskDir, "etc", "fstab")
                    fstab = None

                    for fstabname in RecoveryImageMaker.FSTABS:
                        fstabpathcheck =  os.path.join(workRamdiskDir, "etc", fstabname)
                        if os.path.exists(fstabpathcheck):
                            fstab = Fstab.parseFstab(fstabpathcheck)
                            break

                    if fstab is None:
                        raise ValueError("Couldn't parse any of /etc/{%s}" % (",".join(RecoveryImageMaker.FSTABS)))

                    diffMounts = ConfigSyncer.diffMounts(self.getConfig(), fstab)
                    for k, v in diffMounts.items():
                        self.getConfig().setRecursive(k, v)

                    if not os.path.exists(fstabPath) and self.getMakeValue("inject_fstab", True):
                        self.injectFstab(fstab, workRamdiskDir)

                    result = super(RecoveryImageMaker, self).make(workDir, outDir)
                    self.setValue("recovery.img", recoveryImg.getValue())
                return result

    def overrideDmVerityHash(self, ramdiskDir):
        target = os.path.join(ramdiskDir, "sbin", "dm_verity_hash")
        if not os.path.exists(target):
            return
        with open(target,'w') as f:
            f.write("#!/sbin/sh\n")
            f.write("exit 0;\n")
        os.chmod(target, 493)


    def readProps(self, ramdiskDir):
        from inception.common.propfile import DefaultPropFile
        props = DefaultPropFile(os.path.join(ramdiskDir, "default.prop"))
        self.setTargetConfigValue("arch", props.getArch(), diffOnly=True)

    def injectFstab(self, fstab, ramdiskDir):
            fstabPath = os.path.join(ramdiskDir, "etc", "fstab")
            with open(fstabPath, "w") as fstabOut:
                fstabOut.write(fstab.__str__())

    def injectBusyBox(self, ramDiskDir):
        busyboxKey, busybox = self.getTargetBinary("busybox")
        if busybox is None:
            logger.error("Must set %s to busybox path" % busyboxKey)
            sys.exit(1)
        busyBoxSymlinks = BusyboxSubmaker.SYMLINKS

        busyboxSbin = os.path.join(ramDiskDir, "sbin", "busybox")
        if os.path.exists(busyboxSbin):
            logger.warn("busybox already exists as /sbin/busybox, going to overwrite")
        shutil.copy(busybox, busyboxSbin)
        os.chmod(busyboxSbin, 493)
        for link in busyBoxSymlinks:
            linkPath = os.path.join(os.path.dirname(busyboxSbin), link)
            try:
                os.symlink(os.path.basename(busyboxSbin), linkPath)
            except OSError:
                logger.warn("%s already exists, skipping" % linkPath)


        return True

    def injectKeys(self, ramdDiskDir):
        keysName = self.config.get("update.keys", None)
        if not keysName:
            raise ValueError("recovery.inject_keys is set to true, but update.keys is not set")
        elif keysName == "test":
            if not self.config.get("update.restore_stock_recovery"):
                logger.warning("\n========================\n\nWARNING: You requested inception to inject 'test' keys inside the recovery image. "
                               "It's advised to either set update.restore_stock_recovery=true or use your own keys, "
                               "otherwise anyone can install their own update packages through the modified recovery.\n\n========================")

        signingKeys = self.getConfig().getKeyConfig(keysName)
        assert signingKeys, "update.keys is '%s' but __config__.host.keys.%s is not set" % (keysName, keysName)
        pubPath = unicode(signingKeys["public"])
        keysVal = dumppublickey.print_rsa(pubPath)

        return self.injectKey(os.path.join(ramdDiskDir, self.__class__.PATH_KEYS), keysVal)

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
