from .maker import Maker
from inception.constants import InceptionConstants
import os
class ConfigMaker(Maker):
    def __init__(self, config):
        super(ConfigMaker, self).__init__(config, "config")
    def make(self, workDir, outDir):
        configOutPath = os.path.join(outDir, InceptionConstants.OUT_NAME_CONFIG)
        with open(configOutPath, 'w') as configOut:
            configOut.write(self.config.dumpFullData())

        return configOutPath