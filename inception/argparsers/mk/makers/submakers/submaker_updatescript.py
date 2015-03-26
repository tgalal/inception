from .submaker import Submaker
from inception.generators.updatescript import UpdateScriptGenerator
import os
class UpdatescriptSubmaker(Submaker):
    def make(self, updatePkgDir):
        u = UpdateScriptGenerator()
        u.setVerbose(self.getConfigValue("script.verbose", True))

        #### mount needed FS
        u.mount("/system")
        u.mount("/data")

        #### remove files
        for f in self.getConfigValue("files.rm", []):
            u.rm(f)

        for f in self.getConfigValue("files.rmdir", []):
            u.rm(f, True)

        #### format?
        if  self.getMaker().getConfig().get("data.format", False):
            u.rm("/data", recursive=True)

        #### extract our FS
        for f in os.listdir(updatePkgDir):
            target = "/" + f
            if os.path.isdir(os.path.join(updatePkgDir,f)):
                u.extractDir(target[1:], target)
            else:
                u.extractFile(target[1:], target)

        #### apply our FS permissions

        for path, pathData in self.getConfigValue("files.add", {}).items():
            destPath = pathData["destination"]
            if not destPath.startswith("/"):
                destPath = "/" + destPath

            localPath = updatePkgDir + destPath
            if not os.path.exists(localPath):
                    raise Exception("Cannot set permissions for a missing file: " + destPath)

            permState = ("mode" in pathData, "uid" in pathData, "gid" in pathData)
            if any(permState):
                if not all(permState):
                    print(pathData)
                    raise Exception("Missing permission data for " + destPath)

                if os.path.isdir(updatePkgDir + destPath):
                    u.setPermissions(destPath, pathData["uid"], pathData["gid"], pathData["mode"], pathData["mode_dirs"])
                else:
                    u.setPermissions(destPath, pathData["uid"], pathData["gid"], pathData["mode"])

        #### misc
        header, footer = self.getConfigValue("script.header", None), self.getConfigValue("script.footer", None)
        wait = self.getConfigValue("script.wait", 0)
        if header is not None:
            u.setHeader(header)
        if footer is not None:
            u.setFooter(footer)

        if wait > 0:
            u.setPostExecutionWait(wait)

        #### post, pre install scripts
        pre, post = self.getConfigProperty("script.pre", None), self.getConfigProperty("script.post", None)
        preScript = postScript = ""
        if pre.getValue():
            preFile = pre.getConfig().resolveRelativePath(pre.getValue())
            with open(preFile, "r") as preFileHandler:
                preScript = preFileHandler.read()

        if post.getValue():
            postFile = post.getConfig().resolveRelativePath(post.getValue())
            with open(postFile, "r") as postFileHandler:
                postScript = postFileHandler.read()

        updateScriptDir = os.path.join(updatePkgDir, "META-INF", "com","google","android")
        os.makedirs(updateScriptDir)
        with open(os.path.join(updateScriptDir, "updater-script"), "w") as updateScriptFile:
            if preScript:
                updateScriptFile.write(preScript)
                updateScriptFile.write("\n")
            updateScriptFile.write(u.generate())

            if postScript:
                updateScriptFile.write("\n")
                updateScriptFile.write(postScript)