from .submaker import Submaker
import os
import sys
import  logging
logger = logging.getLogger(__name__)
class UpdatescriptSubmaker(Submaker):
    def make(self, updatePkgDir, updatescriptgen = None):
        u = updatescriptgen

        #### remove files
        for path in self.getValue("files.rm", []):
            if not path.startswith("/"):
                path = "/" + path
            u.rm(path)

        for path in self.getValue("files.rmdir", []):
            if not path.startswith("/"):
                path = "/" + path
            u.rm(path, recursive = True)


        #### apply our FS permissions

        extractedDirs = []

        addFilesDict = self.getValue("files.add", {})
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

            if "__depend__" in pathData and pathData["__depend__"]:
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
                if not dirname.startswith("/dev/") and dirname not in extractedDirs:
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
                    if "symlinks" in pathData:
                        for i in range(0, len(pathData["symlinks"]), 5):
                            edge = i + 5
                            if edge >= len(pathData["symlinks"]):
                                edge = len(pathData["symlinks"]) - 1

                            u.symlink(destPath, pathData["symlinks"][i:edge])

                if "context" in pathData:
                    u.setContext(destPath, pathData["context"])


        #### misc
        header, footer = self.getValue("script.header", None), self.getValue("script.footer", None)
        wait = self.getValue("script.wait", 0)
        if header is not None:
            u.setHeader(header)
        if footer is not None:
            u.setFooter(footer)

        if wait > 0:
            u.setPostExecutionWait(wait)

        #### post, pre install scripts

        postscripts = self.__getFullResolvedInstScriptList("post")
        prescripts = self.__getFullResolvedInstScriptList("pre")

        for script in prescripts:
            with open(script, "r") as prescriptFile:
                u.addPrescript(prescriptFile.read().strip())

        for script in postscripts:
            with open(script, "r") as postscriptFile:
                u.addPostscript(postscriptFile.read().strip())


        updateScriptDir = os.path.join(updatePkgDir, "META-INF", "com","google","android")
        os.makedirs(updateScriptDir)
        with open(os.path.join(updateScriptDir, "updater-script"), "w") as updateScriptFile:


            updateScriptFile.write(u.generate(self.getValue("script.progress", True)))


    def __getFullResolvedInstScriptList(self, key):
        result = []
        currConfig = self.getProperty("script." + key).getConfig()
        result.extend(self.__getResolvedInstScriptsList(key, currConfig))
        while not currConfig.isOrphan():
            currConfig = currConfig.getParent()
            result.extend(self.__getResolvedInstScriptsList(key, currConfig))
        return result

    def __getResolvedInstScriptsList(self, key, config):
        curr = config.getProperty("update.script." + key, [], directOnly=True)
        return [curr.resolveRelativePath(script) for script in curr.getValue()]