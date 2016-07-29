from .maker import Maker
from .submakers.submaker_wifi import WifiSubmaker
from .submakers.submaker_fs import FsSubmaker
from .submakers.submaker_updatescript import UpdatescriptSubmaker
from .submakers.submaker_property import PropertySubmaker
from .submakers.submaker_updatezip import UpdatezipSubmaker
from .submakers.submaker_adbkeys import AdbKeysSubmaker
from .submakers.submaker_apps import AppsSubmaker
from .submakers.submaker_supersu import SuperSuSubmaker
from .submakers.submaker_databases import DatabasesSubmaker
from .submakers.submaker_settings import SettingsSubmaker
from .submakers.submaker_updatescriptinit import UpdatescriptInitSubmaker
from .submakers.submaker_busybox import BusyboxSubmaker
from inception.generators.updatescript import UpdateScriptGenerator
import shutil
import os
import logging
logger = logging.getLogger(__name__)
class UpdateMaker(Maker):
    def __init__(self, config):
        super(UpdateMaker, self).__init__(config, "update")
        self.rootFs = "fs"
        self.updatescriptGen = UpdateScriptGenerator(
            self.getTargetConfigValue("bin.update-binary.config.metadata_supported", False)
        )

    def make(self, workDir, outDir):
        logger.info("Making update package")
        rootFS = os.path.join(workDir, self.rootFs)
        self.makeUpdateScriptInit(rootFS)
        self.makeFS(rootFS)
        self.makeProps(rootFS)
        self.makeWPASupplicant(rootFS)
        self.makeBusyBox(rootFS)
        self.makeSettings(rootFS)
        self.makeDatabases(rootFS)
        self.makeAdbKeys(rootFS)
        self.makeStockRecovery(rootFS)
        self.makeRoot(rootFS)
        self.makeApps(rootFS)
        self.makeUpdateScript(rootFS)
        return self.makeUpdateZip(rootFS, outDir)

    def isMakeTrue(self, key):
        return self.getMakeValue(key + ".__make__", True)

    def makeFS(self, fsPath):
        logger.info("Making FS")
        if not os.path.exists(fsPath):
            os.makedirs(fsPath)

        smaker = FsSubmaker(self, "files")
        smaker.make(fsPath)


    def makeBusyBox(self, fsPath):
        if self.isMakeTrue("busybox"):
            logger.info("Making Busybox")
            smaker = BusyboxSubmaker(self, "busybox")
            smaker.make(fsPath, self.updatescriptGen)

    def makeRoot(self, fsPath):
        rootMethod = self.getMakeValue("root_method", None)

        if rootMethod:
            logger.info("Selected root method: %s" % rootMethod)
            if rootMethod == "supersu":
                return self.makeSuperSu(fsPath)

            raise ValueError("Unknown root method %s" % rootMethod)


    def makeSuperSu(self, fsPath):
        if self.isMakeTrue("supersu"):
            logger.info("Making SuperSU")
            smaker = SuperSuSubmaker(self, ".")
            smaker.make(fsPath)

    def makeSettings(self, workDir):
        if self.isMakeTrue("settings"):
            logger.info("Making Settings")
            smaker = SettingsSubmaker(self, "settings")
            smaker.make(workDir)
        else:
            self.setValue("update.settings", {"__override__": True})

    def makeDatabases(self, workDir):
        if self.isMakeTrue("databases"):
            logger.info("Making databases")
            smaker = DatabasesSubmaker(self, "databases")
            smaker.make(workDir)
        else:
            self.setValue("update.databases", {"__override__": True})

    def makeWPASupplicant(self, workDir):
        if self.isMakeTrue("network"):
            logger.info("Making WPASupplicant")
            wpaSupplicantDir = os.path.join(workDir, "data", "misc", "wifi")
            smaker = WifiSubmaker(self, "network")
            smaker.make(wpaSupplicantDir)


    def makeUpdateScriptInit(self, updatePkgDir):
        logger.info("Init Update script")
        smaker = UpdatescriptInitSubmaker(self, ".")
        smaker.make(updatePkgDir, self.updatescriptGen)

    def makeUpdateScript(self, updatePkgDir):
        logger.info("Making Update script")
        smaker = UpdatescriptSubmaker(self, ".")
        smaker.make(updatePkgDir, self.updatescriptGen)

    def makeProps(self, workDir):
        if self.isMakeTrue("property"):
            logger.info("Making /data/property")
            smaker = PropertySubmaker(self, "property")
            smaker.make(workDir)

    def makeAdbKeys(self, workDir):
        if self.isMakeTrue("adb"):
            logger.info("Making ADB keys")
            smaker = AdbKeysSubmaker(self, "adb")
            smaker.make(workDir)

    def makeStockRecovery(self, workDir):
        if self.getMakeValue("restore_stock_recovery", False):
            logger.info("Making Stock recovery")
            stockRecProp = self.getConfig().getProperty("recovery.stock")
            assert stockRecProp.getValue() is not None, "recovery.stock is not specified"
            stockRecPath = stockRecProp.getConfig().resolveRelativePath(stockRecProp.getValue())
            assert os.path.isfile(stockRecPath), "%s does not exist" % stockRecPath
            recoveryDev = self.getConfig().getMountConfig("recovery.dev", None)
            assert recoveryDev, "__config__.target.mount.recovery.dev is not specified"

            stockRecoveryData = {
                "destination": recoveryDev
            }

            workDirRecPath = os.path.join(workDir, "stockrec.img")
            shutil.copy(stockRecPath, workDirRecPath)
            self.setValue("update.files.add.stockrec\.img", stockRecoveryData)

    def makeApps(self, workDir):
        if self.isMakeTrue("apps"):
            logger.info("Making Apps")
            smaker = AppsSubmaker(self, "apps")
            smaker.make(workDir)

    def makeUpdateZip(self, work, outDir):
        logger.info("Making Update zip")
        smake = UpdatezipSubmaker(self, ".")
        updateZipPkgPath = smake.make(work)
        shutil.copy(updateZipPkgPath, outDir)
        return os.path.join(outDir, os.path.basename(updateZipPkgPath))