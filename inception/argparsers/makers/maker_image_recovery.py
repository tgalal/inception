from .maker_image import ImageMaker
import shutil
import os
from inception.constants import InceptionConstants
class RecoveryImageMaker(ImageMaker):
    def __init__(self, config):
        super(RecoveryImageMaker, self).__init__(config, "recovery", InceptionConstants.OUT_NAME_RECOVERY)

    def make(self, workDir, outDir):
        # if self.getMakeConfigValue("include_update"):
        #     ramdDiskTarget = os.path.join(workDir, "recovery_ramdisk")
        #     updatezipTargetDir = os.path.join(ramdDiskTarget, "update")
        #     ramdDiskSrc = self.getMakeConfigValue("img.ramdisk")
        #     cacheDev = self.getConfig().get("cache.dev")
        #
        #     assert cacheDev, "cache.dev must be set for including update in recovery to function"
        #
        #     assert os.path.exists(os.path.join(ramdDiskSrc, "sbin", "busybox")),\
        #         "Busybox must be present in ramdisk for including update in recovery to function"
        #     shutil.copytree(ramdDiskSrc, ramdDiskTarget, symlinks=True)
        #
        #     recoveryBin = os.path.join(ramdDiskTarget, "sbin", "recovery")
        #     recoveryBinOrig = recoveryBin + ".orig"
        #     shutil.copy(recoveryBin, recoveryBinOrig)
        #
        #     os.makedirs(updatezipTargetDir)
        #     shutil.copy(os.path.join(outDir, InceptionConstants.OUT_NAME_UPDATE), updatezipTargetDir)
        #
        #     with open(recoveryBin, "w") as f:
        #         f.write("#!/sbin/busybox sh\n")
        #         f.write("mount %s /cache\n" % cacheDev)
        #         f.write("echo \"--update_package=/update/%s\" > /cache/recovery/command\n" % InceptionConstants.OUT_NAME_UPDATE)
        #         f.write("/sbin/%s\n" % os.path.basename(recoveryBinOrig))
        #
        #
        #     self.setConfigValue("recovery.img.ramdisk", ramdDiskTarget)
        #
        #     result = super(RecoveryImageMaker, self).make(workDir, outDir)
        #
        #     fsize = os.path.getsize(os.path.join(outDir, InceptionConstants.OUT_NAME_RECOVERY))
        #     maxSize = self.getMakeConfigValue("size", fsize)
        #
        #     assert fsize < maxSize, "Output recovery img is greater than max size and won't work"
        #
        #     return result
        # else:
        #     return super(RecoveryImageMaker, self).make(workDir, outDir)

        return super(RecoveryImageMaker, self).make(workDir, outDir)
