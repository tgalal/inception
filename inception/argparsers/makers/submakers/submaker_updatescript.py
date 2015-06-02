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
        if  self.getConfigValue("script.format_data", False):
            u.rm("/data", recursive=True)


        for path in self.getConfigValue("files.rm", []):
            if not path.startswith("/"):
                path = "/" + path
            u.rm(path)

        for path in self.getConfigValue("files.rmdir", []):
            if not path.startswith("/"):
                path = "/" + path
            u.rm(path, recursive = True)

        #### apply our FS permissions

        extractedDirs = []

        addFilesDict = self.getConfigValue("files.add", {})
        paths = sorted(addFilesDict.keys())
        for path in paths:
            pathData = addFilesDict[path]
            if "destination" in pathData:
                destPath = pathData["destination"]
            elif path[0] == "/":
                destPath = path
            else:
                raise Exception("No destination specified for %s" % path)
            if not destPath.startswith("/"):
                destPath = "/" + destPath

            if path.startswith("/"):
                path = path[1:]

            localPath = updatePkgDir + "/" + path

            if "__depend__" in pathData:
                if self.getMaker().getConfig().get(pathData["__depend__"]) is None:
                    continue
                else:
                    dependTargetMake = self.getMaker().getConfig().get(pathData["__depend__"] + ".__make__", True)
                    if not dependTargetMake:
                        continue
            if not os.path.exists(localPath):
                    raise Exception("Cannot set permissions for a missing file: " + localPath)


            if os.path.isdir(localPath):
                u.extractDir(path, destPath)
                extractedDirs.append(destPath)
            else:
                dirname = os.path.dirname(destPath)
                if dirname not in extractedDirs:
                    u.extractDir(os.path.dirname(path), dirname)
                    extractedDirs.append(dirname)
                u.extractFile(path, destPath)


            permState = ("mode" in pathData, "uid" in pathData, "gid" in pathData)
            if any(permState):
                if not all(permState):
                    raise Exception("Missing permission data for " + destPath)

                if "mode_dirs" in pathData:
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

        postscripts = self.__getFullResolvedInstScriptList("post")
        prescripts = self.__getFullResolvedInstScriptList("pre")

        updateScriptDir = os.path.join(updatePkgDir, "META-INF", "com","google","android")
        os.makedirs(updateScriptDir)
        with open(os.path.join(updateScriptDir, "updater-script"), "w") as updateScriptFile:
            for script in prescripts:
                with open(script, "r") as prescriptFile:
                    updateScriptFile.write("\n")
                    updateScriptFile.write(prescriptFile.read())

            updateScriptFile.write(u.generate(showProgress=self.getConfigValue("script.progress", True)))

            for script in postscripts:
                with open(script, "r") as postscriptFile:
                    updateScriptFile.write("\n")
                    updateScriptFile.write(postscriptFile.read())

    def __getFullResolvedInstScriptList(self, key):
        result = []
        currConfig = self.getConfigProperty("script." + key).getConfig()
        result.extend(self.__getResolvedInstScriptsList(key, currConfig))
        while not currConfig.isOrphan():
            currConfig = currConfig.getParent()
            result.extend(self.__getResolvedInstScriptsList(key, currConfig))
        return result

    def __getResolvedInstScriptsList(self, key, config):
        curr = config.getProperty("update.script." + key, [], directOnly=True)
        return [curr.resolveRelativePath(script) for script in curr.getValue()]