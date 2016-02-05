from .argparser import InceptionArgParser
from .exceptions import InceptionArgParserException
from inception.constants import InceptionConstants
from inception.common.configsyncer import ConfigSyncer
from inception.tools import imgtools
import os, shutil, logging
from inception.config import ConfigTreeParser, DotIdentifierResolver
from inception.common.fstabtools import Fstab
from inception.config.configv2 import ConfigV2
from inception.common.propfile import DefaultPropFile
import sys
logger = logging.getLogger(__name__)
class BootstrapArgParser(InceptionArgParser):

    def __init__(self):
        super(BootstrapArgParser, self).__init__(description = "Bootstrap a variant config, based on an existing base "
                                                               "config, or based on another variant config")
        requiredOpts = self.add_argument_group("Required args")

        requiredOpts.add_argument('-b', '--base', required = True, action = "store", help="base config code to use, in the format A.B")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store", help="variant config code to use, in the format A.B.C")


        optionalOpts = self.add_argument_group("Optional args")
        optionalOpts.add_argument("-r", '--recovery', required = False, action="store", help="Use the supplied recovery img in bootstraped config")
        optionalOpts.add_argument("-u", '--unpack-recovery', required = False, action="store_true", help="Unpack recovery if it exists/supplied")
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


        if self.config.get("__config__") is None:
            sys.stderr.write("You are using an outdated config tree. Please run 'incept sync -v VARIANT_CODE' or set __config__ (see https://goo.gl/aFWPby)\n")
            sys.exit(1)

        self.configDir = self.config.getSource(getDir=True)
        baseCodePath= "/".join(self.args["base"].split(".")[:2])
        self.variantDir = os.path.join(self.deviceDir, baseCodePath, self.args["variant"])

        logger.info("Writing new config")
        self.newConfig = self.createNewConfig(self.args["base"] + "." + self.args["variant"], self.args["variant"], self.config)
        self.setupDirPaths()
        self.createDirs()

        unpackerKey, unpacker = self.config.getHostBinary("unpackbootimg")
        bootImg = self.config.getProperty("boot.img", None)
        if bootImg and self.config.get("boot.__make__", False):
            if type(bootImg.getValue()) is str:
                logger.info("Unpacking boot img")
                self.unpackimg(bootImg.getConfig().resolveRelativePath(bootImg.getValue()), self.bootDir, unpacker, "boot")


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
                if self.newConfig.getMountConfig("recovery.dev"):
                    logger.info("pulling recovery.img")
                    syncer.syncImg("recovery.img", self.newConfig.getMountConfig("recovery.dev"), imgsDir, self.variantDir)
                else:
                    logger.warn("__config__.target.mount.recovery.dev not set, not syncing recovery.img")

                if self.newConfig.getMountConfig("boot.dev"):
                    logger.info("pulling boot.img")
                    syncer.syncImg("boot.img", self.newConfig.getMountConfig("boot.dev"), imgsDir, self.variantDir)
                else:
                    logger.warn("__config__.target.mount.boot.dev not set, not syncing boot.img")


        recoveryPath = None
        if self.args["recovery"]:
            recoveryPath = os.path.join(self.imgDir, os.path.basename(self.args["recovery"]))
            self.createDir(self.imgDir)
            shutil.copy(self.args["recovery"], recoveryPath)
            relPath =  os.path.relpath(recoveryPath, self.variantDir)
            self.newConfig.set("recovery.img", relPath)

        if self.args["unpack_recovery"]:
            recoveryImg = self.newConfig.getProperty("recovery.img", None)
            if type(recoveryImg.getValue()) is str:
                logger.info("Unpacking recovery img")
                self.unpackimg(recoveryPath or recoveryImg.getConfig().resolveRelativePath(recoveryImg.getValue()), self.recoveryDir, unpacker, "recovery")
            else:
                logger.warning("recovery is already unpacked at a parent")

        configPath = self.writeNewConfig(self.args["variant"])

        logger.info("Created %s" % configPath)

        return True

    def createNewConfig(self, identifier, name, baseConfig):
        return ConfigV2.new(identifier, name, baseConfig)

    def writeNewConfig(self, name):
        out = os.path.join(self.variantDir, "%s.json" % name)
        newConfigFile = open(out, "w")
        newConfigFile.write(self.newConfig.dumpContextData())
        newConfigFile.close()

        return out

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
        bootImgGenerator  = imgtools.unpackimg(unpacker, img, out)

        self.newConfig.set("%s.img.cmdline" % imgType, bootImgGenerator.getKernelCmdLine(quote=False))
        self.newConfig.set("%s.img.base" % imgType, bootImgGenerator.getBaseAddr())
        self.newConfig.set("%s.img.ramdisk_offset" % imgType, bootImgGenerator.getRamdiskOffset())
        self.newConfig.set("%s.img.second_offset" % imgType, bootImgGenerator.getSecondOffset())
        self.newConfig.set("%s.img.tags_offset" % imgType, bootImgGenerator.getTagsOffset())
        self.newConfig.set("%s.img.pagesize" % imgType, bootImgGenerator.getPageSize())
        self.newConfig.set("%s.img.second_size" % imgType, bootImgGenerator.getSecondSize())
        self.newConfig.set("%s.img.dt_size" % imgType, bootImgGenerator.getDeviceTreeSize())
        self.newConfig.set("%s.img.kernel" % imgType, os.path.relpath(bootImgGenerator.getKernel(), self.variantDir))
        self.newConfig.set("%s.img.ramdisk" % imgType, os.path.relpath(bootImgGenerator.getRamdisk(), self.variantDir))
        self.newConfig.set("%s.img.dt" % imgType, os.path.relpath(bootImgGenerator.getDeviceTree(), self.variantDir))


        etcPath = os.path.join(out, bootImgGenerator.getRamdisk(), "etc")
        fstabFilename = None
        if os.path.exists(etcPath):
            for f in os.listdir(etcPath):
                if f.endswith("fstab"):
                    fstabFilename = f

            if fstabFilename is None:
                raise ValueError("Couldn't locate fstab")

            fstab = Fstab.parseFstab(os.path.join(etcPath, fstabFilename))

            processParts = ("boot", "kernel", "system", "recovery", "cache")

            for p in processParts:
                fstabPart = fstab.getByMountPoint("/" + p)
                if not fstabPart:
                    continue
                key = "__config__.target.mount.%s." % p
                if self.newConfig.get(key + "dev") != fstabPart.getDevice():
                    self.newConfig.set(key + "dev", fstabPart.getDevice())

                if self.newConfig.get(key + "mount") != fstabPart.getMountPoint():
                    self.newConfig.set(key + "mount", fstabPart.getMountPoint())

                if self.newConfig.get(key + "fs") != fstabPart.getType():
                    self.newConfig.set(key + "fs", fstabPart.getType())


        defaultProp = DefaultPropFile(os.path.join(out, bootImgGenerator.getRamdisk(), "default.prop"))

        if defaultProp.getArch():
            self.newConfig.setTargetConfigValue("arch", defaultProp.getArch(), diffOnly=True)

        if defaultProp.getProductManufacturer():
            self.newConfig.setTargetConfigValue("device.manufacturer", defaultProp.getProductManufacturer(), diffOnly=True)

        if defaultProp.getProductBrand():
            self.newConfig.setTargetConfigValue("device.brand", defaultProp.getProductBrand(), diffOnly=True)

        if defaultProp.getProductBoard():
            self.newConfig.setTargetConfigValue("device.board", defaultProp.getProductBoard(), diffOnly=True)

        if defaultProp.getProductDevice():
            self.newConfig.setTargetConfigValue("device.name", defaultProp.getProductDevice(), diffOnly=True)
