from .maker import Maker
from inception.generators.cacheimg import CacheImgGenerator
import os
from inception.constants import InceptionConstants
import logging
import shutil
logger = logging.getLogger(__name__)

class SystemMaker(Maker):
    DEFAULT_MAKE = False
    def __init__(self, config):
        super(SystemMaker, self).__init__(config, "system")

    def make(self, workDir, outDir):
        prop = self.getMakeProperty("img")

        fname = self.getSystemOutName()
        shutil.copy(prop.resolveAsRelativePath(), os.path.join(outDir, fname))
        return os.path.join(outDir, fname)
