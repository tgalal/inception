from argparser import InceptionArgParser
from exceptions import InceptionArgParserException
from ..generators import BootImgGenerator
from .. import InceptionConstants
from .. import Configurator
from .. import InceptionExecCmdFailedException
import os, subprocess, json, shutil

class BootstrapArgParser(InceptionArgParser):

    def __init__(self):
        super(BootstrapArgParser, self).__init__(description = "Bootstrap mode cmd")
        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-b', '--base', required = True, action = "store")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store")
        #requiredOpts.add_argument('-v', '--vendor', required = True, action = "store")
        #requiredOpts.add_argument('-m', '--model', required = True, action = "store")

        optionalOpts = self.add_argument_group("Optional args")
        optionalOpts.add_argument("-f", "--force", required = False, action = "store_true")
        optionalOpts.add_argument('-s', '--standalone', required = False, action = "store_true")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR

    def process(self):
        super(BootstrapArgParser, self).process()
        self.createDir(self.deviceDir)

        self.configurator = Configurator(self.args["base"])

        self.configDir = os.path.dirname(self.configurator.getConfigPath())
        self.config = self.configurator.getConfig()
        vendor = self.configurator.getConfigVendor()
        model = self.configurator.getConfigModel()

        

        if self.args["standalone"] == False:
            self.d("Writing new config")
            self.newConfig = self.createNewConfig(self.args["variant"], self.configurator.getConfig())
        else:
            self.d("Writing standalone config")
            self.newConfig = self.createNewConfig(self.args["variant"], self.configurator.getConfig(), True)

        self.setupDirPaths(vendor, model, self.args["variant"])
        self.d("Creating dirs")
        self.createDirs()
        
        #self.unpackimg(bootImg, self.bootDir, self.config["tools"]["unpackbootimg"], "boot")

        unpacker = self.newConfig.get("config.unpackbootimg.bin") 
        
        if self.config.get("imgs.boot", None):
            self.d("Unpacking boot img")
            bootImg = "%s/%s" % (self.configDir, self.config.get("imgs.boot"))
            self.unpackimg(bootImg, self.bootDir, unpacker, "boot")       
            self.createDir(self.bootDir)
        

        if  self.config.get("imgs.recovery"):
            recoveryImg = "%s/%s" % (self.configDir, self.config.get("imgs.recovery"))
            self.d("Unpacking recovery img")
            self.unpackimg(recoveryImg, self.recoveryDir, unpacker, "recovery")
            self.createDir(self.recoveryDir)

        

        self.writeNewConfig(self.args["variant"])

        self.writeCmdLog(os.path.join(self.variantDir, "bootstrap.commands.log"))


        return True


    def createNewConfig(self, name, baseConfig , standalone = False):

        newConfigContent = self.configurator.createConfigTemplate(name, baseConfig = None if standalone else baseConfig)

        if standalone == True:
            newConfigContent = self.configurator.createConfigFromTree([self.configurator.getConfig().getData(), newConfigContent])

        return newConfigContent

    def writeNewConfig(self, name):
        newConfigFile = open(os.path.join(self.variantDir, "%s.json" % name), "w")
        newConfigFile.write(self.newConfig.toString())
        newConfigFile.close()

    def findBaseConfig(self, configName):
        #look inside device for specified id
        #return if found else:
        #look inside base
        #return if found else:
        #error

        self.d("Looking for", configName, "in", self.deviceDir)
        vendors = os.listdir(self.deviceDir)
        for v in vendors:
            modelsDir = self.createPathString(self.deviceDir, v)
            models = os.listdir(modelsDir)
            self.d("Entering", modelsDir)
            for m in models:
                variantsDir = self.createPathString(modelsDir, m)
                variants = os.listdir(variantsDir)

                configPath = self.createPathString(variantsDir, configName, "%s.json" % configName)
                self.d("Checking", configPath)
                if os.path.exists(configPath):
                    return (v, m, configPath)

        self.d("Looking for", configName, "in", self.baseDir)
        vendors = os.listdir(self.baseDir)
        for v in vendors:
            modelsDir = self.createPathString(self.baseDir, v)
            models = os.listdir(modelsDir)
            configPath = self.createPathString(modelsDir, configName, "%s.json" % configName)
            self.d("Checking", configPath)
            if os.path.exists(configPath):
                return (v, configName, configPath)

        return None

    def createPathString(self, *args):
        return "/".join(args)

    def setupDirPaths(self, vendor, model, variant):
        self.vendorDir          = self.createPathString(self.deviceDir, vendor)
        self.modelDir           = self.createPathString(self.vendorDir, model)
        self.variantDir         = self.createPathString(self.modelDir, variant)
        self.imgDir             = self.createPathString(self.variantDir, "img")
        self.bootDir            = self.createPathString(self.imgDir, "boot")
        self.recoveryDir        = self.createPathString(self.imgDir, "recovery")
        self.fsDir              = self.createPathString(self.variantDir, InceptionConstants.FS_DIR)



    def createDirs(self):
        self.createDir(self.vendorDir)
        self.createDir(self.modelDir)
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
        return self.createPathString(self.configDir, configName + ".config")

    def setupConfigDirs(self):
        self.createDir(self.configDir)
        self.d("Creating build config")
        buildConfig = open(self.getConfigPath("build"), "w")
        buildConfigData = BootstrapArgParser.BUILD_DEFCONFIG.format(mkbootimg = "mkbootimg", unpackbootimg = self.args["unpacker"], make_ext4fs = "make_ext4fs")
        buildConfig.write(buildConfigData)
        buildConfig.close()

        self.d("Creating wpa_supplicant template")
        wpasupConfig = open(self.getConfigPath("wpa_supplicant"), "w")
        wpasupConfig.write("#place here wpa_supplicant.conf header\n")
        wpasupConfig.close()

        self.d("Creating system apk rm config")
        systemAppRmConfig = open(self.getConfigPath("system.app.rm"), "w")
        systemAppRmConfig.write("#place here apks names to delete from system\n")
        systemAppRmConfig.close()

        self.d("Creating update-pkg permissions config")
        permConfig = open(self.getConfigPath("permissions"), "w")
        permConfig.write("#place here permissions to use when creating update-pkg\n")
        permConfig.close()



    def unpackimg(self, img, out, unpacker, imgType):
        filename = img.split('/')[-1]
        ramdisk = "%s/%s-ramdisk" % (out, filename)
        kernel = "%s/%s-zImage" % (out, filename)
        dt = "%s/%s-dt" % (out, filename)
        ramdiskDir = self.createPathString(out, "ramdisk")
        ramdiskExtracted = ramdiskDir + "/" + filename + "-ramdisk"

        unpackResult = self.execCmd(unpacker, "-i", img, "-o", out, failMessage = "Failed to unpack %s to %s" % (img, out))
        try:
            self.execCmd("gunzip", ramdisk + ".gz") 
        except InceptionExecCmdFailedException, e:
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
                self.newConfig.setProperty("config.%s.cmdline" % imgType, value)
            elif key == "BOARD_KERNEL_BASE":
                self.newConfig.setProperty("config.%s.base" % imgType, "0x" + value)
            elif key == "BOARD_RAMDISK_OFFSET":
                self.newConfig.setProperty("config.%s.ramdisk_offset" % imgType, "0x" + value)
            elif key == "BOARD_SECOND_OFFSET":
                self.newConfig.setProperty("config.%s.second_offset" % imgType, "0x" + value)
            elif key == "BOARD_TAGS_OFFSET":
                self.newConfig.setProperty("config.%s.tags_offset" % imgType, "0x" + value)
            elif key == "BOARD_PAGE_SIZE":
                self.newConfig.setProperty("config.%s.pagesize" % imgType, int(value))
            elif key == "BOARD_SECOND_SIZE":
                self.newConfig.setProperty("config.%s.second_size" % imgType, int(value))
            elif key == "BOARD_DT_SIZE":
                self.newConfig.setProperty("config.%s.dt_size" % imgType, int(value))


        self.newConfig.setProperty("config.%s.kernel" % imgType, kernel)
        self.newConfig.setProperty("config.%s.ramdisk" % imgType, ramdiskDir)
        self.newConfig.setProperty("config.%s.dt" % imgType, dt)



       



