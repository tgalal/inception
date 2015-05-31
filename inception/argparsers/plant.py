from .argparser import InceptionArgParser
from .make import MakeArgParser
from .exceptions import InceptionArgParserException
from inception.constants import InceptionConstants
from inception.config.dotidentifierresolver import DotIdentifierResolver
from inception.config.configtreeparser import ConfigTreeParser
from inception.tools.heimdall import Heimdall
from inception.tools.rkflashtool import RkFlashTool
import os
import logging

logger = logging.getLogger(__name__)

class PlantArgParser(InceptionArgParser):

    IMGS = ("boot", "cache", "recovery")

    def __init__(self):
        super(PlantArgParser, self).__init__(description = "Plant mode cmd")
        self.flashers = ("heimdall", "rkflash", "dd", "cat")

        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store")
        requiredOpts.add_argument('-t', '--through', required = True, action = "store", metavar="(%s)" % ("|".join(self.getFlashers())))

        optionalOpts = self.add_argument_group("Plant options")
        optionalOpts.add_argument('-m', '--make', required = False, action = "store_true")

        imageOptions = self.add_argument_group("Plant images")
        imageOptions.add_argument('-b', '--boot', required = False, action = "store_false")
        imageOptions.add_argument('-c', '--cache', required = False, action = "store_false")
        imageOptions.add_argument('-r', '--recovery', required = False, action = "store_false")

        identifierResolver = DotIdentifierResolver([InceptionConstants.VARIANTS_DIR, InceptionConstants.BASE_DIR])
        self.configTreeParser = ConfigTreeParser(identifierResolver)

    def getFlashers(self):
        return self.flashers

    def process(self):
        print("plant is still WIP")
        return True
        super(PlantArgParser, self).process()

        self.config = self.configTreeParser.parseJSON(self.args["variant"])
        self.setOutDir(self.config.getOutPath())

        argImgs = (self.args[img] for img in self.__class__.IMGS)
        if not all(argImgs):
            for img in argImgs:
                self.args[img] = not self.args

        if self.args["make"]:
            m = MakeArgParser()
            if not m.make(self.args["variant"]):
                raise InceptionArgParserException("Make failed")

        if self.args["through"] == "heimdall":
            return self.processHeimdall()
        elif self.args["through"] == "dd":
            return self.processDataDestroyer()
        elif self.args["through"] == "rkflash":
            return self.processRkflash()
        elif self.args["through"] == "cat":
            return self.processCat()
        else:
            raise InceptionArgParserException("Unsupported plant method: %s " % self.args["through"])

    def getFlashDict(self):
        flashDict = {}

        for img in self.__class__.IMGS:
            imgPath = self.getOutDir() + "/%s.img" % img
            if os.path.exists(imgPath):
                flashDict[img] = (self.config.get("fstab.%s.dev" % img), imgPath)
            else:
                logger.warn("Args contain %s but there was no %s" % (img, imgPath))

        return flashDict

    def processRkflash(self):
        r = RkFlashTool(self.config.get("config.rkflashtool.bin"))
        flashDict = {}

        def add(t):
            flashDict[self.config.get("fstab.%s.pit_name" % t)] = self.getOutDir() + "/%s.img" % t
        if self.args["boot"]:
            add("boot")
        if self.args["recovery"]:
            add("recovery")
        if self.args["cache"]:
            add("cache")

        r.flash(**flashDict)
        return True

    def processDataDestroyer(self):
        flashDict = self.getFlashDict()
        targetTmp = "/sdcard/inception_dd"
        cache = self.config.get("fstab.cache")
        recovery = self.config.get("fstab.recovery")
        
        adb = self.getAdb(self.config.get("config.adb.bin"), busybox=self.config.get("config.adb.busybox"))
        adb.mkdir(targetTmp)

        for imgName, imgData in flashDict.items():
            device, img = imgData
            self.d("Pushing " + img)
            targetImgPath = targetTmp + "/" + os.path.basename(img)
            adb.push(img, targetImgPath)

        for imgName, imgData in flashDict.items():
            device, img = imgData
            self.d("Flashing %s to %s" % (targetImgPath, device))
            devices = adb.devices()
            deviceMode = devices.itervalues().next()

            cmd = (
                "dd",
                "if=%s" % targetImgPath,
                "of=%s" % device,
            )

            adb.cmd(*cmd, su = self.config.get("config.adb.require-su", False) and deviceMode == "device")
        adb.rmdir(targetTmp)

        return True


    def processCat(self):
        flashDict = {}
        targetTmp = "/sdcard/inception_dd"
        cache = self.config.get("fstab.cache")
        recovery = self.config.get("fstab.recovery")
        
        adb = self.getAdb(self.config.get("config.adb.bin"))
        adb.mkdir(targetTmp)

        def add(t):
            flashDict[self.config.get("fstab.%s.dev" % t)] = self.getOutDir() + "/%s.img" % t

        if self.args["boot"]:
            add("boot")
        if self.args["recovery"]:
            add("recovery")
        if self.args["cache"]:
            add("cache")

        for device, img in flashDict.items():
            self.d("Pushing " + img)
            targetImgPath = targetTmp + "/" + os.path.basename(img)
            adb.push(img, targetTmp)

        for device, img in flashDict.items():
            self.d("Flashing %s to %s" % (targetImgPath, device))
            devices = adb.devices()
            deviceMode = devices.itervalues().next()
            adb.cmd(
                "cat",
                targetImgPath,
                ">",
                device,
                su = self.config.get("config.adb.require-su", False) and deviceMode == "device"
            )
            adb.cmd(
                "sync"
            )
            adb.cmd(
                "sync"
            )
            adb.cmd(
                "sync"
            )

        adb.rmdir(targetTmp)

        return True

    def processHeimdall(self):
        h = Heimdall(self.config.get("config.heimdall.bin"))
        flashDict = {}

        def add(t):
            flashDict[self.config.get("fstab.%s.pit_name" % t)] = self.getOutDir() + "/%s.img" % t

        if self.args["boot"]:
            add("boot")
        if self.args["recovery"]:
            add("recovery")
        if self.args["cache"]:
            add("cache")

        h.flash(**flashDict)
        return True
