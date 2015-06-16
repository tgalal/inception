from .submaker import Submaker
class UpdatescriptInitSubmaker(Submaker):
    def make(self, updatePkgDir, updatescriptGen = None):
        updatescriptGen.setVerbose(self.getValue("script.verbose", True))
        updatescriptGen.setVerbose(self.getValue("script.verbose", True))

        #### mount needed FS
        updatescriptGen.mount("/system")
        updatescriptGen.mount("/data")

