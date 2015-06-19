from .argparser import InceptionArgParser
from inception.constants import InceptionConstants
from inception.config import configtreeparser
from inception.config.dotidentifierresolver import DotIdentifierResolver
import logging
logger = logging.getLogger(__name__)

class SyncArgParser(InceptionArgParser):

    def __init__(self):
        super(SyncArgParser, self).__init__(description = "Sync config tree")

        requiredOpts = self.add_argument_group("Required args")
        codeOpts = requiredOpts.add_mutually_exclusive_group(required = True)
        codeOpts.add_argument('-b', '--base', action = "store", help="variant config code to use, in the format A.B")
        codeOpts.add_argument('-v', '--variant', action = "store", help="variant config code to use, in the format A.B.C")
        requiredOpts.add_argument('-f', '--force', required = False, action="store_true")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = configtreeparser.ConfigTreeParser(identifierResolver)

    def process(self):
        super(SyncArgParser, self).process()
        if not self.args["force"]:
            logger.warning("This will overwrite any changes in your base configs. "
                       "Everything under %s will be overwritten. Use -f to force." % InceptionConstants.BASE_DIR)
            return True

        config = self.configTreeParser.parseJSON(self.args["variant"] or self.args["base"])

        while not config.isOrphan():
            config = config.getParent()
            if not config.isBase():
                continue
            self.configTreeParser.syncRepo(config.getSource(True))

        return True