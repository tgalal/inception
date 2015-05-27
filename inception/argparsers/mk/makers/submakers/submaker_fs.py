from .submaker import Submaker
import os, shutil, sys
class FsSubmaker(Submaker):
    def make(self, workDir):
        fsSourcePaths = []
        fsSourceMap = {}
        lookupFPaths = []

        configProp = self.getConfigProperty("add", {})
        currConfig = self.getMaker().getConfig()
        for path in configProp.getValue().keys():
            lookupFPaths.append(path)

        while not currConfig.isOrphan():
            currConfig = currConfig.getParent()
            for path in currConfig.get("update.files.add", {}).keys():
                if path not in lookupFPaths:
                    lookupFPaths.append(path)

        currConfig = self.getMaker().getConfig()
        for path in lookupFPaths:
            fsSourcePaths.append((os.path.join(currConfig.getFSPath(), path), currConfig.get("update.files.add.%s" % (path.replace(".", "\.")))))

        while not currConfig.isOrphan():
            currConfig = currConfig.getParent()
            for path in lookupFPaths:
                key = "update.files.add.%s" % (path.replace(".", "\."))
                pathInfo = currConfig.get(key, None)
                if pathInfo:
                    fsSourcePaths.append((os.path.join(currConfig.getFSPath(), path), pathInfo))

        fsSourcePaths.reverse()
        # print("Going to merge the following dirs")
        # print("\n".join(fsSourcePaths))
        # for srcPath in fsSourcePaths:
        #     if os.path.exists(srcPath):
        #         self._recursiveOverwrite(srcPath, workDir)

        written = []

        for src in fsSourcePaths:
            srcPath, pathInfo = src
            if os.path.exists(srcPath):
                if "destination" in pathInfo:
                    destPath = pathInfo["destination"]
                    if destPath.startswith("/"):
                        destPath = destPath[1:]
                    target = os.path.join(workDir, destPath)

                    # if not os.path.exists(srcPath):
                    #     if destPath not in written:
                    #         print("%s doesn't exist" % srcPath)
                    #         sys.exit(1)
                    #     else:
                    #         continue
                    self._recursiveOverwrite(srcPath, target)
                    written.append(destPath)
                else:
                    print("Error destination for %s is not set" % srcPath)
                    sys.exit(1)


    def _recursiveOverwrite(self, src, dest, ignore=None):
        if os.path.isdir(src):
            if not os.path.isdir(dest):
                os.makedirs(dest)
            files = os.listdir(src)
            if ignore is not None:
                ignored = ignore(src, files)
            else:
                ignored = set()
            for f in files:
                if f not in ignored:
                    self._recursiveOverwrite(os.path.join(src, f),
                                        os.path.join(dest, f),
                                        ignore)
        else:
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            shutil.copyfile(src, dest)


