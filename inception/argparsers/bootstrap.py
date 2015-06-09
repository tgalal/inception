from .argparser import InceptionArgParser
from .exceptions import InceptionArgParserException
from inception.constants import InceptionConstants
from inception.inceptionobject import InceptionExecCmdFailedException
from inception.common.configsyncer import ConfigSyncer
import os, shutil, logging
from inception.config import ConfigTreeParser, DotIdentifierResolver, Config

logger = logging.getLogger(__name__)
class BootstrapArgParser(InceptionArgParser):

    def __init__(self):
        super(BootstrapArgParser, self).__init__(description = "Bootstrap a variant config, based on an existing base "
                                                               "config, or based on another variant config")
        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-b', '--base', required = True, action = "store", help="base config code to use, in the format A.B")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store", help="variant config code to use, in the format A.B.C")
        #requiredOpts.add_argument('-v', '--vendor', required = True, action = "store")
        #requiredOpts.add_argument('-m', '--model', required = True, action = "store")

        optionalOpts = self.add_argument_group("Optional args")
        optionalOpts.add_argument('--learn-settings', action="store_true",
                                  help="Learn settings from a connected device, and set in the bootstrapped config file" )

        optionalOpts.add_argument("--learn-props", action = "store_true",
                                  help="Learn update.property from a connected device, and set in the bootstrapped config file")

        optionalOpts.add_argument("--learn-partitions", action = "store_true",
                                  help="Learn information about partitions on device, and set in the bootstrapped config file")

        optionalOpts.add_argument("--learn-imgs", action = "store_true",
                                  help="Pull recovery and boot img from the device, and set in the bootstrapped config file")

        optionalOpts.add_argument("-f", "--force", required = False, action = "store_true", help="Overwrite an existing variant bootstrap directory if exists")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        self.configTreeParser = ConfigTreeParser(DotIdentifierResolver([self.deviceDir, self.baseDir]))

    def process(self):
        super(BootstrapArgParser, self).process()
        self.createDir(self.deviceDir)
        self.config = self.configTreeParser.parseJSON(self.args["base"])
        self.configDir = self.config.getSource(getDir=True)

        baseCodePath= "/".join(self.args["base"].split(".")[:2])

        self.variantDir = os.path.join(self.deviceDir, baseCodePath, self.args["variant"])

        logger.info("Writing new config")
        self.newConfig = self.createNewConfig(self.args["base"] + "." + self.args["variant"], self.args["variant"], self.config)
        self.setupDirPaths()
        self.createDirs()
        #self.unpackimg(bootImg, self.bootDir, self.config["tools"]["unpackbootimg"], "boot")

        unpackerProperty = self.config.getProperty("common.tools.unpackbootimg.bin")
        unpacker = unpackerProperty.getConfig().resolveRelativePath(unpackerProperty.getValue())
        bootImg = self.config.getProperty("boot.img", None)
        if bootImg and self.config.get("boot.make", False):
            if type(bootImg.getValue()) is str:
                logger.info("Unpacking boot img")
                self.unpackimg(bootImg.getConfig().resolveRelativePath(bootImg.getValue()), self.bootDir, unpacker, "boot")


        recoveryImg = self.config.getProperty("recovery.img", None)
        if recoveryImg and self.config.get("recovery.make", False):
            if type(recoveryImg.getValue()) is str:
                logger.info("Unpacking recovery img")
                self.unpackimg(recoveryImg.getConfig().resolveRelativePath(recoveryImg.getValue()), self.recoveryDir, unpacker, "recovery")


        if any((self.args["learn_settings"], self.args["learn_partitions"], self.args["learn_props"], self.args["learn_imgs"])):
            syncer = ConfigSyncer(self.newConfig)
            if self.args["learn_settings"]:
                logger.info("pulling settings")
                syncer.applyDiff(syncer.pullAndDiff())
            if self.args["learn_partitions"]:
                logger.info("pulling partitions info")
                syncer.syncPartitions(True)
            if self.args["learn_props"]:
                logger.info("pulling props")
                syncer.syncProps(True)

            if self.args["learn_imgs"]:
                imgsDir = os.path.join(self.variantDir, "imgs")
                os.makedirs(imgsDir)
                if self.newConfig.get("recovery.dev"):
                    logger.info("pulling recovery.img")
                    syncer.syncImg("recovery.img", self.newConfig.get("recovery.dev"), imgsDir, self.variantDir)
                else:
                    logger.warn("recovery.dev not set, not syncing recovery.img")

                if self.newConfig.get("boot.dev"):
                    logger.info("pulling boot.img")
                    syncer.syncImg("boot.img", self.newConfig.get("boot.dev"), imgsDir, self.variantDir)
                else:
                    logger.warn("boot.dev not set, not syncing boot.img")

        self.writeNewConfig(self.args["variant"])

        self.writeCmdLog(os.path.join(self.variantDir, "bootstrap.commands.log"))


        return True

    def createNewConfig(self, identifier, name, baseConfig):
        return Config.new(identifier, name, baseConfig)


    def writeNewConfig(self, name):
        newConfigFile = open(os.path.join(self.variantDir, "%s.json" % name), "w")
        newConfigFile.write(self.newConfig.dumpContextData())
        newConfigFile.close()

    def createDir(self, d):
        if not os.path.exists(d):
            logger.info("Creating: %s" % d)
            os.makedirs(d)
        else:
            logger.info("Exists: %s" % d)

    def setupDirPaths(self):
        self.imgDir             = os.path.join(self.variantDir, "img")
        self.bootDir            = os.path.join(self.imgDir, "boot")
        self.recoveryDir        = os.path.join(self.imgDir, "recovery")
        self.fsDir              = os.path.join(self.variantDir, InceptionConstants.FS_DIR)

    def createDirs(self):
        # self.createDir(self.variantDir)
        if os.path.exists(self.variantDir):
            if self.args["force"]:
                shutil.rmtree(self.variantDir)
            else:
                raise InceptionArgParserException("%s exists!!" % self.variantDir)

        self.createDir(self.variantDir)
        self.createDir(self.fsDir)


    def getAbsolutePathOf(self, f):
        return os.path.dirname(os.path.realpath(__file__)) + "/" + f 

    def getConfigPath(self, configName):
        return os.path.join(self.configDir, configName + ".config")

    def unpackimg(self, img, out, unpacker, imgType):
        if not os.path.isfile(img):
            raise ValueError("Coudn't find %s to unpack"  % img)
        filename = img.split('/')[-1]
        ramdisk = "%s/%s-ramdisk" % (out, filename)
        kernel = "%s/%s-zImage" % (out, filename)
        dt = "%s/%s-dt" % (out, filename)
        ramdiskDir = os.path.join(out, "ramdisk")
        ramdiskExtracted = ramdiskDir + "/" + filename + "-ramdisk"
        os.makedirs(out)
        unpackResult = self.execCmd(unpacker, "-i", img, "-o", out, failMessage = "Failed to unpack %s to %s" % (img, out))
        try:
            self.execCmd("gunzip", ramdisk + ".gz") 
        except InceptionExecCmdFailedException as e:
            self.execCmd("mv", ramdisk + ".gz", ramdisk + ".xz")
            self.execCmd("unxz", ramdisk + ".xz")

        self.createDir(ramdiskDir)
        self.execCmd("mv", ramdisk, ramdiskDir)

        f = open(ramdiskExtracted)
        try:
            self.execCmd("cpio", "-i", cwd = ramdiskDir, stdin = f)
        finally:
            f.close()
        os.remove(ramdiskExtracted)

        #process unpacker output
        resultList = unpackResult.split('\n')
        for l in resultList:
            try:
                dissect = l.split(' ')
                key = dissect[0]
                value = " ".join(dissect[1:]) or None
            except ValueError:
                key = l.split(' ')
                value = None

            if key == "BOARD_KERNEL_CMDLINE":
                self.newConfig.set("%s.img.cmdline" % imgType, value)
            elif key == "BOARD_KERNEL_BASE":
                self.newConfig.set("%s.img.base" % imgType, "0x" + value)
            elif key == "BOARD_RAMDISK_OFFSET":
                self.newConfig.set("%s.img.ramdisk_offset" % imgType, "0x" + value)
            elif key == "BOARD_SECOND_OFFSET":
                self.newConfig.set("%s.img.second_offset" % imgType, "0x" + value)
            elif key == "BOARD_TAGS_OFFSET":
                self.newConfig.set("%s.img.tags_offset" % imgType, "0x" + value)
            elif key == "BOARD_PAGE_SIZE":
                self.newConfig.set("%s.img.pagesize" % imgType, int(value))
            elif key == "BOARD_SECOND_SIZE":
                self.newConfig.set("%s.img.second_size" % imgType, int(value))
            elif key == "BOARD_DT_SIZE":
                self.newConfig.set("%s.img.dt_size" % imgType, int(value))


        self.newConfig.set("%s.img.kernel" % imgType, os.path.relpath(kernel, self.variantDir))
        self.newConfig.set("%s.img.ramdisk" % imgType, os.path.relpath(ramdiskDir, self.variantDir))
        self.newConfig.set("%s.img.dt" % imgType, os.path.relpath(dt, self.variantDir))



       



