from .maker import Maker
from .submakers.submaker_wifi import WifiSubmaker
from .submakers.submaker_fs import FsSubmaker
import os
class UpdateMaker(Maker):
    def __init__(self, config):
        super(UpdateMaker, self).__init__(config, "update")
        self.rootFs = "fs"

    def make(self, workDir, outDir):
        rootFS = os.path.join(workDir, self.rootFs)
        self.makeFS(rootFS)
        self.makeWPASupplicant(rootFS)

    def makeFS(self, fsPath):
        if not os.path.exists(fsPath):
            os.makedirs(fsPath)

        smaker = FsSubmaker(self, "files")
        smaker.make(fsPath)

    def makeSettings(self):
        pass

    def makeWPASupplicant(self, workDir):
        wpaSupplicantDir = os.path.join(workDir, "data", "misc", "wifi")
        smaker = WifiSubmaker(self, "network")
        smaker.make(wpaSupplicantDir)