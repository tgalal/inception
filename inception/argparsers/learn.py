from inception.argparsers.argparser import InceptionArgParser
from inception.constants import InceptionConstants
from inception.config import configtreeparser
from inception.common.moduletools import ModuleTools
from inception.common.configsyncer import ConfigSyncer
from inception.config.dotidentifierresolver import DotIdentifierResolver
from inception.common.filetools import FileTools
import json
import logging
import os

logger = logging.getLogger(__name__)

class LearnArgParser(InceptionArgParser):

    def __init__(self):
        super(LearnArgParser, self).__init__(description = "Analyzes settings from a connected device via USB,"
                                                           " and outputs only the diff data that you'd need to update "
                                                           "the specified variant's config file to match the connected one's")

        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store", help="variant config code to use, in the format A.B.C")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = configtreeparser.ConfigTreeParser(identifierResolver)

    def process(self):
        super(LearnArgParser, self).process()

        resultDict = {
            "update": {}
        }

        self.config = self.configTreeParser.parseJSON(self.args["variant"])
        self.learnPartitions()
        learntSettings = self.learnSettings()
        resultDict["update"]["settings"] = learntSettings["settings"]
        resultDict["update"]["databases"] = learntSettings["databases"]
        resultDict["update"]["property"] = self.learnProps()
        resultDict.update(self.learnPartitions())
        print(json.dumps(resultDict, indent = 4))
        logger.info("Printed new and different settings, manually add to your config json file if needed")
        return True

    def learnProps(self):
        syncer = ConfigSyncer(self.config)
        return syncer.syncProps()

    def learnSettings(self):
        syncer = ConfigSyncer(self.config)
        diff = syncer.pullAndDiff()
        return diff

    def learnPartitions(self):
        syncer = ConfigSyncer(self.config)
        return syncer.syncPartitions()



