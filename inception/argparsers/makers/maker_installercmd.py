from .maker import Maker
from inception.constants import InceptionConstants
import os
class InstallerCmdMaker(Maker):
    def __init__(self, config):
        super(InstallerCmdMaker, self).__init__(config, "installercmd")
    def make(self, workDir, outDir):
        allIncludes = {}
        excludes = self.getMakeValue("exclude", [])
        if "cache" not in excludes:
            allIncludes["cache"] = self.getCacheOutName()

        if "recovery" not in excludes:
            allIncludes["recovery"] = InceptionConstants.OUT_NAME_RECOVERY

        if "boot" not in excludes:
            allIncludes["boot"] = InceptionConstants.OUT_NAME_BOOT

        outPath = os.path.join(outDir, "installer.cmd")

        with open(outPath, "w") as f:
            if self.getMakeValue("unlock", False):
                f.write("oem unlock\n")
            for name, path in allIncludes.items():
                f.write("flash:%s#/installer/%s" % (name, path))
                f.write("\n")

            f.write(self.getConfig().getTargetConfigValue("bin.fastboot.config.boot_recovery_command", "continue") + "\n")

        return outPath