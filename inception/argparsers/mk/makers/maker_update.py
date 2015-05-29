from .maker import Maker
from .submakers.submaker_wifi import WifiSubmaker
from .submakers.submaker_fs import FsSubmaker
from .submakers.submaker_updatescript import UpdatescriptSubmaker
from .submakers.submaker_keyvaldb_settings import SettingsKeyValDBSubmaker
from .submakers.submaker_property import PropertySubmaker
from .submakers.submaker_updatezip import UpdatezipSubmaker
from .submakers.submaker_adbkeys import AdbKeysSubmaker
from .submakers.submaker_apps import AppsSubmaker
import shutil
import os
import logging
logger = logging.getLogger(__name__)
class UpdateMaker(Maker):
    def __init__(self, config):
        super(UpdateMaker, self).__init__(config, "update")
        self.rootFs = "fs"

    def make(self, workDir, outDir):
        logger.info("Making update package")
        rootFS = os.path.join(workDir, self.rootFs)
        self.makeFS(rootFS)
        self.makeProps(rootFS)
        self.makeWPASupplicant(rootFS)
        self.makeSettings(rootFS)
        self.makeAdbKeys(rootFS)
        self.makeStockRecovery(rootFS)
        self.makeApps(rootFS)
        self.makeUpdateScript(rootFS)
        self.makeUpdateZip(rootFS, outDir)

    def makeFS(self, fsPath):
        logger.info("Making FS")
        if not os.path.exists(fsPath):
            os.makedirs(fsPath)

        smaker = FsSubmaker(self, "files")
        smaker.make(fsPath)

    def makeSettings(self, workDir):
        logger.info("Making Settings databases")
        smaker = SettingsKeyValDBSubmaker(self, "settings")
        smaker.make(workDir)

    def makeWPASupplicant(self, workDir):
        logger.info("Making WPASupplicant")
        wpaSupplicantDir = os.path.join(workDir, "data", "misc", "wifi")
        smaker = WifiSubmaker(self, "network")
        smaker.make(wpaSupplicantDir)

    def makeUpdateScript(self, updatePkgDir):
        logger.info("Making Update script")
        smaker = UpdatescriptSubmaker(self, ".")
        smaker.make(updatePkgDir)

    def makeProps(self, workDir):
        logger.info("Making /data/property")
        smaker = PropertySubmaker(self, "property")
        smaker.make(workDir)

    def makeAdbKeys(self, workDir):
        logger.info("Making ADB keys")
        smaker = AdbKeysSubmaker(self, "adb")
        smaker.make(workDir)

    def makeStockRecovery(self, workDir):
        if self.getMakeConfigValue("restore_stock", False):
            logger.info("Making Stock recovery")
            stockRecProp = self.getConfig().getProperty("recovery.stock")
            assert stockRecProp.getValue() is not None, "recovery.stock is not specified"
            stockRecPath = stockRecProp.getConfig().resolveRelativePath(stockRecProp.getValue())
            assert os.path.isfile(stockRecPath), "%s does not exist" % stockRecPath
            recoveryDev = self.getConfig().get("recovery.dev", None)
            assert recoveryDev, "recovery.dev is not specified"

            stockRecoveryData = {
                "destination": recoveryDev
            }

            workDirRecPath = os.path.join(workDir, "stockrec.img")
            shutil.copy(stockRecPath, workDirRecPath)
            self.setConfigValue("update.files.add.stockrec\.img", stockRecoveryData)

    def makeApps(self, workDir):
        logger.info("Making Apps")
        smaker = AppsSubmaker(self, "apps")
        smaker.make(workDir)

    def makeUpdateZip(self, work, outDir):
        logger.info("Making Update zip")
        smake = UpdatezipSubmaker(self, ".")
        updateZipPkgPath = smake.make(work)
        shutil.copy(updateZipPkgPath, outDir)