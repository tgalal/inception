from .argparser import InceptionArgParser
from inception.constants import InceptionConstants
from inception.config import configtreeparser
from inception.config.dotidentifierresolver import DotIdentifierResolver
import logging
import os

logger = logging.getLogger(__name__)

class LsArgParser(InceptionArgParser):
    FLAGS_KEYS = ("cache", "odin", "boot", "recovery", "update")
    KEY_OUTS_MAP = {
        "cache":    InceptionConstants.OUT_NAME_CACHE,
        "odin":     InceptionConstants.OUT_NAME_ODIN,
        "boot":     InceptionConstants.OUT_NAME_BOOT,
        "recovery": InceptionConstants.OUT_NAME_RECOVERY,
        "update":   InceptionConstants.OUT_NAME_UPDATE
    }

    FLAGS_SEPARATOR = ""

    def __init__(self):
        super(LsArgParser, self).__init__(description = "list available configs")
        self.time = False
        viewOpts = self.add_argument_group("View mode").add_mutually_exclusive_group()
        viewOpts.add_argument("-l", '--long', action="store_true", help = "Long listing")
        # viewOpts.add_argument("-t", '--tree', action="store_true")

        requiredOpts = self.add_argument_group("Config types").add_mutually_exclusive_group()
        requiredOpts.add_argument('-v', '--variants', action = "store_true", help = "List variant configs only")
        requiredOpts.add_argument('-b', '--bases', action="store_true", help = "List base configs only")
        requiredOpts.add_argument('-a', '--all',  action="store_true", help = "List all configs")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = configtreeparser.ConfigTreeParser(identifierResolver)

        self.longest = 0

    def process(self):
        super(LsArgParser, self).process()

        if self.args["all"]:
            self.listVariants(self.args["long"])
            print("")
            self.listBases(self.args["long"])
        elif self.args["variants"]:
            self.listVariants(self.args["long"])
        elif self.args["bases"]:
            self.listBases(self.args["long"])
        else:
            self.listVariants(self.args["long"])

        return True

    def listVariants(self, long = False):
        print("Variants:")
        print("=========")
        variants = self.searchDir(InceptionConstants.VARIANTS_DIR, 3)
        if long:
            self.listLong(variants)
        else:
            print("\n".join(sorted(variants.keys())))

    def listBases(self, long = False):
        print("Bases:")
        print("=========")
        bases = self.searchDir(InceptionConstants.BASE_DIR, 2)
        if long:
            self.listLong(bases)
        else:
            print("\n".join(sorted(bases.keys())))

    def listLong(self, d):
        keys = sorted(d.keys())
        if not len(keys):
            print("")
            return
        longestKey = max( len(x) for x in keys )
        self.longest = max(longestKey, self.longest)
        for key in keys:
            flags = self.getFlags(d[key]) if not d[key].isBase() else [" " for i in self.__class__.FLAGS_KEYS]
            formattedFlags = self.formatFlags(flags)
            print("%*s %*s %s" % (-self.longest, key, -len(self.__class__.FLAGS_KEYS) , formattedFlags, d[key].getSource()))

    def searchDir(self, path, depth, currDepth = 0):
        keysDict = {}

        if currDepth == depth:
            configPath = os.path.join(path, os.path.basename(path) + ".json")
            if os.path.exists(configPath):
                keys = path.split("/")[-depth:]
                code = ".".join(keys)
                try:
                    return {code:  self.configTreeParser.parseJSONFile(configPath, code)}
                except ValueError as e:
                    logger.warning("Coudn't parse json %s" % configPath)
                    return {}

        elif os.path.isdir(path):
            for f in os.listdir(path):
                keysDict.update(self.searchDir(os.path.join(path, f), depth, currDepth+1))

        return keysDict

    def formatFlags(self, flags):
        return self.__class__.FLAGS_SEPARATOR.join(flags)

    def getFlags(self, config):
        flags = []
        for key in self.__class__.FLAGS_KEYS:
            outPath = os.path.join(config.getOutPath(), self.__class__.KEY_OUTS_MAP[key])

            if key == "odin":
                outPath = outPath.format(identifier = config.getIdentifier().replace(".", "-"))
                if config.get("odin.checksum", True):
                    outPath += ".md5"

            if os.path.exists(outPath):
                flags.append(key[0].lower())
            else:
                flags.append("-")

        return flags
