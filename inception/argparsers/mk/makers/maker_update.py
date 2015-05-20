from .maker import Maker
from .submakers.submaker_wifi import WifiSubmaker
from .submakers.submaker_fs import FsSubmaker
from .submakers.submaker_updatescript import UpdatescriptSubmaker
from .submakers.submaker_keyvaldb_settings import SettingsKeyValDBSubmaker
from .submakers.submaker_property import PropertySubmaker
from .submakers.submaker_updatezip import UpdatezipSubmaker
import shutil
import os
class UpdateMaker(Maker):
    def __init__(self, config):
        super(UpdateMaker, self).__init__(config, "update")
        self.rootFs = "fs"

    def make(self, workDir, outDir):
        rootFS = os.path.join(workDir, self.rootFs)
        self.makeFS(rootFS)
        self.makeProps(rootFS)
        self.makeWPASupplicant(rootFS)
        self.makeSettings(rootFS)
        self.makeUpdateScript(rootFS)
        self.makeUpdateZip(rootFS, outDir)

    def makeFS(self, fsPath):
        if not os.path.exists(fsPath):
            os.makedirs(fsPath)

        smaker = FsSubmaker(self, "files")
        smaker.make(fsPath)

    def makeSettings(self, workDir):
        smaker = SettingsKeyValDBSubmaker(self, "settings")
        smaker.make(workDir)

    def makeWPASupplicant(self, workDir):
        wpaSupplicantDir = os.path.join(workDir, "data", "misc", "wifi")
        smaker = WifiSubmaker(self, "network")
        smaker.make(wpaSupplicantDir)

    def makeUpdateScript(self, updatePkgDir):
        smaker = UpdatescriptSubmaker(self, ".")
        smaker.make(updatePkgDir)

    def makeProps(self, workDir):
        smaker = PropertySubmaker(self, "property")
        smaker.make(workDir)

    def makeUpdateZip(self, work, outDir):
        smake = UpdatezipSubmaker(self, ".")
        updateZipPkgPath = smake.make(work)
        shutil.copy(updateZipPkgPath, outDir)