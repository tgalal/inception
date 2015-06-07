from inception.argparsers.argparser import InceptionArgParser
from inception.argparsers.exceptions import InceptionArgParserException, MakeUpdatePkgFailedException
from inception.constants import InceptionConstants
from inception.config import ConfigTreeParser, DotIdentifierResolver
import os, shutil, logging
from inception.common.configsyncer import ConfigSyncer

logger = logging.getLogger(__name__)

class MakeArgParser(InceptionArgParser):

    def __init__(self, description = "Make mode cmd"):
        super(MakeArgParser, self).__init__(description = description)

        targetOpts = self.add_mutually_exclusive_group(required = True)
        targetOpts.add_argument('-v', '--variant',action = "store", help="variant config code to use, in the format A.B.C")

        optionalOpts = self.add_argument_group("Optional opts")
        optionalOpts.add_argument('--learn-settings', action="store_true",
                                  help= "Learn settings from a connected device, and use in generated update package")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = ConfigTreeParser(identifierResolver)

    def process(self):
        super(MakeArgParser, self).process()

        code = self.args["variant"]

        try:
            self.vendor, self.model, self.variant = code.split('.')
        except ValueError as e:
            raise InceptionArgParserException(
                "Code must me in the format vendor.model.variant"
                )

        self.setWorkDir(os.path.join(InceptionConstants.WORK_DIR,
            self.vendor,
            self.model,
            self.variant))
        self.setOutDir(os.path.join(InceptionConstants.OUT_DIR,
            self.vendor,
            self.model,
            self.variant))
        self.workDir = self.getWorkDir()
        self.config = self.configTreeParser.parseJSON(code)

        if self.config.get("__abstract__", False, directOnly=True):
            print("Won't make abstract config %s" % code)
            return True

        self.configDir = os.path.dirname(self.config.getSource())

        logger.info("Cleaning work dir " + self.workDir)
        if os.path.exists(self.workDir):
            shutil.rmtree(self.workDir)
        os.makedirs(self.workDir)

        logger.info("Cleaning out dir")
        outDir = self.getOutDir()
        if os.path.exists(outDir):
            shutil.rmtree(outDir)
        os.makedirs(outDir)


        if self.args["learn_settings"]:
            syncer = ConfigSyncer(self.config)
            syncer.applyDiff(syncer.pullAndDiff())

        self.config.make(self.workDir)

        self.writeUsedConfig()

        return True

    def writeUsedConfig(self):
        f = open(os.path.join(self.getOutDir(), "config.json"), "w")
        f.write(self.config.dumpFullData())
        f.close()

