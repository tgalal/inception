from .maker import Maker
class BootMaker(Maker):
    def __init__(self, config):
        super(BootMaker, self).__init__(config, "boot")
    def make(self, workDir, outDir):
        pass