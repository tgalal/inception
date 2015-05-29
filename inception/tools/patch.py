from .execwrapper import ExecWrapper
import os
class Patch(ExecWrapper):
    def __init__(self):
        super(Patch, self).__init__("patch")

    def patch(self, path, patchFile, strip = 0):
        patchFile = open(patchFile)
        self.setArg("p", str(strip))
        self.setCwd(path)
        self.setStdIn(patchFile)
        self.run()
        patchFile.close()
