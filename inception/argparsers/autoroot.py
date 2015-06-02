from .argparser import InceptionArgParser
from inception.constants import InceptionConstants
from inception.config import configtreeparser
from inception.config.dotidentifierresolver import DotIdentifierResolver
import logging
from inception.config import Config
logger = logging.getLogger(__name__)
import tempfile
from inception.common.filetools import FileTools
import os
import shutil
import sys
class AutorootArgParser(InceptionArgParser):

    def __init__(self):
        super(AutorootArgParser, self).__init__(description = "Autoroot mode cmd")

        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-b', '--base', required = True, action = "store")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = configtreeparser.ConfigTreeParser(identifierResolver)
        self.tmpDir = tempfile.mkdtemp()

    def process(self):
        super(AutorootArgParser, self).process()
        config = self.configTreeParser.parseJSON(self.args["base"])

        config = Config.new(self.args["base"] + ".autoroot", "autoroot", config)
        if os.path.exists(config.getOutPath()):
            shutil.rmtree(config.getOutPath())

        os.makedirs(config.getOutPath())
        config.set("update.restore_stock", True)
        config.set("update.__make__", True)
        config.set("odin.__make__", True)
        config.set("cache.__make__", True)
        config.set("update.root_method", "supersu")
        config.set("update.settings.__make__", False)
        config.set("update.adb.__make__", False)
        config.set("update.property.__make__", False)
        config.set("update.apps.__make__", False)
        config.set("update.network.__make__", False)
        config.set("update.script.format_data", False)

        if not config.get("recovery.stock"):
            print("Autoroot requires having recovery.stock set, and it's not for %s" % self.args["base"])
            sys.exit(1)

        with FileTools.newTmpDir() as workDir:
            config.make(workDir)

        return True
