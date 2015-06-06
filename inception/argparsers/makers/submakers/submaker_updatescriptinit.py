from .submaker import Submaker
class UpdatescriptInitSubmaker(Submaker):
    def make(self, updatePkgDir, updatescriptGen = None):
        updatescriptGen.setVerbose(self.getConfigValue("script.verbose", True))
        updatescriptGen.setVerbose(self.getConfigValue("script.verbose", True))

        #### mount needed FS
        updatescriptGen.mount("/system")
        updatescriptGen.mount("/data")

