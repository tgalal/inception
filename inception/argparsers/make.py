from inception.argparsers.argparser import InceptionArgParser
from inception.argparsers.exceptions import InceptionArgParserException, MakeUpdatePkgFailedException
from inception.constants import InceptionConstants
from inception.config import ConfigTreeParser, DotIdentifierResolver

from .makers.maker_image_boot import BootImageMaker
from .makers.maker_image_recovery import RecoveryImageMaker
from .makers.maker_update import UpdateMaker
from .makers.maker_cache import CacheMaker

import sys, os, json, shutil, threading, logging

logger = logging.getLogger(__name__)


class MakeArgParser(InceptionArgParser):

    def __init__(self, description = "Make mode cmd"):
        super(MakeArgParser, self).__init__(description = description)

        targetOpts = self.add_mutually_exclusive_group(required = True)
        targetOpts.add_argument('-a', '--all',  action = "store_true")
        targetOpts.add_argument('-v', '--variant',action = "store")

        optionalOpts = self.add_argument_group("Optional opts")
        optionalOpts.add_argument("-t", '--threaded',
            required = False,
            action = "store_true")

        # optionalOpts.add_argument("-m", '--write-manifest',
        #     required = False,
        #     action = "store_true")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = ConfigTreeParser(identifierResolver)

        self.makersMap = [
            ("update", UpdateMaker),
            ("boot", BootImageMaker),
            ("recovery", RecoveryImageMaker),
            ("cache", CacheMaker),
        ]

        self.threads = []

    def process(self):
        super(MakeArgParser, self).process()
        self.threaded = self.args["threaded"]


        # if self.args["threaded"]:
        #     print "Threading not implemented yet"
        #     sys.exit(1)
        if self.args["all"]:
            return self.makeAll()

        return self.make(self.args["variant"],
            writeManifest = False, #self.args["write_manifest"],
            )


    def makeAll(self):
        result = {}
        probeDir = InceptionConstants.VARIANTS_DIR
        vendors = os.listdir(probeDir)

        def deferredMake(code):
            maker = MakeArgParser()

            try:
                result[code] = maker.make(code, noCache = self.args["no_cache"])
            except:
                result[code] = False

        for v in vendors:
            models = os.listdir(os.path.join(probeDir, v))
            for m in models:
                variants = os.listdir(os.path.join(probeDir, v, m))
                for c in variants:
                    if not os.path.exists(os.path.join(probeDir, v, m, c, c + ".json")):
                        continue
                    variantCode = "%s.%s.%s" % (v,m,c)
                    if self.threaded:
                        thread = threading.Thread(
                            target = lambda: deferredMake(variantCode)
                            )
                        self.threads.append(thread)
                        thread.start()
                    else:
                        self.make(variantCode,
                            writeManifest = False, #self.args["write_manifest"],
                            )

        for thread in self.threads:
            thread.join()

        print("\n=================\n\nResult:\n")
        for k,v in result.items():
            print("%s\t\t%s" % ("OK" if v else "Failed", k))


        return True


    def make(self, code, writeManifest = False):
        try:
            self.vendor, self.model, self.variant = code.split('.')
        except ValueError as e:
            raise InceptionArgParserException(
                "Code must me in the format vendor.model.variant"
                )

        self.d("MAKING")
        self.d("VENDOR:", self.vendor)
        self.d("MODEL", self.model)
        self.d("VARIANT", self.variant)

        self.setWorkDir(os.path.join(InceptionConstants.WORK_DIR,
            self.vendor,
            self.model,
            self.variant))
        self.setOutDir(os.path.join(InceptionConstants.OUT_DIR,
            self.vendor,
            self.model,
            self.variant))
        self.workDir = self.getWorkDir()
        # try:
        #     self.configurator = Configurator(code)
        # except ConfigNotFoundException as e:
        #     raise InceptionArgParserException(e)

        self.config = self.configTreeParser.parseJSON(code)

        if self.config.get("__abstract__", False, directOnly=True):
            print("Won't make abstract config %s" % code)
            return True

        self.configDir = os.path.dirname(self.config.getSource())
        # self.config = self.configurator.getConfig()
        # self.configDir = os.path.dirname(self.configurator.getConfigPath())


        self.d("Cleaning work dir " + self.workDir)
        if os.path.exists(self.workDir):
            shutil.rmtree(self.workDir)
        os.makedirs(self.workDir)

        self.d("Cleaning out dir")
        outDir = self.getOutDir()
        if os.path.exists(outDir):
            shutil.rmtree(outDir)
        os.makedirs(outDir)


        for makerItem in self.makersMap:
            key, Maker = makerItem
            if self.config.get(key + ".__make__", True):
                m = Maker(self.config)
                m.make(self.workDir, outDir)
            else:
                self.d("Skipping '%s' as it's disabled in config" % key)

        self.writeUsedConfig()

        return True

    def writeUsedConfig(self):
        f = open(os.path.join(self.getOutDir(), "config.json"), "w")
        f.write(self.config.dumpFullData())
        f.close()

