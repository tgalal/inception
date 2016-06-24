from .maker import Maker
import os
import logging
import shutil
logger = logging.getLogger(__name__)

class ExtrasMaker(Maker):
    DEFAULT_MAKE = False
    def __init__(self, config):
        super(ExtrasMaker, self).__init__(config, "extras")

    def make(self, workDir, outDir):
        targetDir = os.path.join(outDir, "extras")
        os.makedirs(targetDir)
        partitions = self.getMakeProperty("img", {})
        result = []
        for partname, path in partitions.value.items():
            imgTargetPath = os.path.join(targetDir, path)
            if not os.path.exists(os.path.dirname(imgTargetPath)):
                os.makedirs(os.path.dirname(imgTargetPath))
            logger.info("Making %s...." % partname)
            shutil.copy(partitions.resolveRelativePath(path), imgTargetPath)
            result.append(imgTargetPath)

        return "\n\t".join(result)
