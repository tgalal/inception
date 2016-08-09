from .maker import Maker
import os
import logging
import shutil
import sys
logger = logging.getLogger(__name__)

PATH_OUT_DNX = "dnx" #deprecated

class DnxMaker(Maker):
    DEFAULT_MAKE = False
    def __init__(self, config):
        super(DnxMaker, self).__init__(config, "dnx")

    def make(self, workDir, outDir):
        targetDir = os.path.join(outDir, self.config.getDnxOutPath())
        os.makedirs(targetDir)

        osLoaderPath = self.getMakeProperty("osloader").resolveAsRelativePath()
        bootPath = self.getMakeProperty("boot").resolveAsRelativePath()

        if not osLoaderPath or not bootPath:
            logger.error("Must set dnx.osloader and dnx.boot to make dnx files.")
            sys.exit(1)

        shutil.copy(osLoaderPath, os.path.join(targetDir, os.path.basename(osLoaderPath)))
        shutil.copy(bootPath, os.path.join(targetDir, os.path.basename(bootPath)))

        return targetDir