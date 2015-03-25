from .submaker import Submaker
from inception.generators.updatescript import UpdateScriptGenerator
class UpdatescriptSubmaker(Submaker):
    def make(self, workDir):
        u = UpdateScriptGenerator()
        formatData = self.getMaker().getConfig().get("data.format", False)
        u.mount("/system")
        u.mount("/data")

        for f in self.getConfigValue("files.rm", []):
            u.rm(f)

        for f in self.getConfigValue("files.rmdir", []):
            u.rm(f, True)

        if formatData:
            u.rm(f, recursive=True)

