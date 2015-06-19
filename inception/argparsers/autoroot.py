from .argparser import InceptionArgParser
from inception.constants import InceptionConstants
from inception.config import configtreeparser
from inception.config.dotidentifierresolver import DotIdentifierResolver
import logging
from inception.config.configv2 import ConfigV2
logger = logging.getLogger(__name__)
from inception.common.filetools import FileTools
import sys
class AutorootArgParser(InceptionArgParser):

    def __init__(self):
        super(AutorootArgParser, self).__init__(description = "Creates Inception Auto-Root package that you can flash to your device. "
                                                              "An Inception Auto-Root package will install root and supersu on your device, "
                                                              "and then reinstalls stock recovery back.")

        requiredOpts = self.add_argument_group("Required args").add_mutually_exclusive_group(required=True)
        requiredOpts.add_argument('-b', '--base', action = "store", help="base config code to use, in the format A.B")
        requiredOpts.add_argument('-v', "--variant", action = "store", help="variant config code to use, in the format A.B.C")


        optionalOpts = self.add_argument_group("Optional args")
        optionalOpts.add_argument("-o", "--output", help="Override default output path")
        optionalOpts.add_argument("--no-recovery", action="store_true", help="Don't make recovery")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = configtreeparser.ConfigTreeParser(identifierResolver)

    def process(self):
        super(AutorootArgParser, self).process()

        identifier = self.args["base"] or self.args["variant"]

        config = self.configTreeParser.parseJSON(identifier)

        if config.get("__config__") is None:
            sys.stderr.write("You are using an outdated config tree. Please run 'incept sync -v VARIANT_CODE' or set __config__ (see https://goo.gl/aFWPby)\n")
            sys.exit(1)

        autorootBase = identifier if config.isBase() else ".".join(identifier.split(".")[:-1])

        config = ConfigV2.new(autorootBase + ".autoroot", "autoroot", config)



        if self.args["output"]:
            config.setOutPath(self.args["output"])

        config.set("update.restore_stock_recovery", True)
        config.set("update.__make__", True)
        config.set("odin.__make__", True)
        config.set("odin.checksum", True)
        config.set("cache.__make__", True)
        config.set("update.databases.__make__", False)
        config.set("update.settings.__make__", False)
        config.set("update.adb.__make__", False)
        config.set("update.property.__make__", False)
        config.set("update.apps.__make__", False)
        config.set("update.network.__make__", False)
        config.set("update.script.format_data", False)
        config.set("update.root_method", "supersu")
        config.set("update.busybox.__make__", False)
        config.set("update.files.__override__", True)
        config.set("update.script.wait", 0)
        config.set("update.keys", "test")
        config.set("recovery.__make__", not self.args["no_recovery"])
        config.set("boot.__make__", False)
        config.set("__config__.target.root.methods.supersu.include_apk", True)
        config.set("__config__.target.root.methods.supersu.include_archs", [])


        if not config.get("recovery.stock"):
            print("Autoroot requires having recovery.stock set, and it's not for %s" % identifier)
            sys.exit(1)

        if not self.args["no_recovery"] and not config.get("recovery.img"):
            logger.error("recovery.img is not set, use --no-recovery to not make recovery")
            sys.exit(1)

        with FileTools.newTmpDir() as workDir:
            config.make(workDir)

        return True
