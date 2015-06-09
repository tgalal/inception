from .submaker import Submaker
import os
import tempfile
from inception.tools.apktool import ApkTool
from inception.tools.patch import Patch
from collections import namedtuple
import shutil
class AppsSubmaker(Submaker):

    def __init__(self, *args, **kwargs):
        super(AppsSubmaker, self).__init__(*args, **kwargs)
        self.patchTools = None
        self.patchTool = Patch()

    def make(self, workDir):
        apps = self.getConfigValue(".", {})
        if "__make__" in apps:
            del apps["__make__"]
        if "__depend__" in apps:
            del apps["__depend__"]
        for pkgName, data in apps.items():
            apkPath = self.getConfigProperty(pkgName.replace(".", "\.") + ".apk").resolveAsRelativePath()
            patchesList = []

            curr = self.getMaker().getConfig()
            patchesKey = "update.apps." + pkgName.replace(".", "\.") + ".patches"
            currPatches = curr.get(patchesKey, [], directOnly=True)
            patchesList.extend([curr.resolveRelativePath(patch) for patch in currPatches if patch != "__override__"])
            if not "__override__" in currPatches:
                while not curr.isOrphan():
                    curr = curr.getParent()
                    currPatches = curr.get(patchesKey, [], directOnly=True)
                    patchesList.extend([curr.resolveRelativePath(patch) for patch in currPatches if patch != "__override__"])
                    if "__override__" in currPatches:
                        break


            dest = "/data/app"
            if "destination" in data:
                dest = data["destination"]
            elif "system" in data and data["system"]:
                dest = "/system/app"


            targetDest = os.path.join(dest[1:] if dest[0] == "/" else dest, os.path.basename(apkPath))
            localDest = os.path.join(workDir, targetDest)

            if not os.path.exists(os.path.dirname(localDest)):
                os.makedirs(os.path.dirname(localDest))

            if len(patchesList):
                if not self.patchTools:
                    apkTool = self.getCommonConfigProperty("tools.apktool.bin", None)
                    assert apkTool.getValue(), "Can't patch APK without apktool. Please set common.tools.apktool.bin"
                    frameworks = self.getCommonConfigProperty("tools.apktool.frameworks_dir", None)
                    assert frameworks.getValue(), "Can't patch APK without common.tools.apktool.frameworks_dir set. " \
                                                  "See http://ibotpeaches.github.io/Apktool/documentation/#frameworks"

                    java = self.getCommonConfigProperty("tools.java.bin")
                    assert java.getValue(), "Can't use apktool without java. Please set common.tools.java.bin"

                    apkTool = apkTool.resolveAsRelativePath()
                    frameworks = frameworks.resolveAsRelativePath()
                    java = java.resolveAsRelativePath()

                    self.patchTools = namedtuple('PatchTools', ['apkTool', 'java', 'frameworks'])(apkTool, java, frameworks)

                self.patchApk(self.patchTools.java,
                              self.patchTools.apkTool,
                              self.patchTools.frameworks,
                              apkPath,
                              patchesList,#[patchesProp.resolveRelativePath(patch) for patch in patches],
                              localDest
                )
            else:
                shutil.copy(apkPath, localDest)

            self.registerApkFile(targetDest)

    def registerApkFile(self, path):
        self.setConfigValue("update.files.add.%s" % (path.replace(".", "\.")), {"destination": "/" + path})

    def patchApk(self, java, apkTool, frameworks, apk,  patches, dest):
        tmpDir = tempfile.mkdtemp()
        try:
            #extract apk
            apkTool = ApkTool(java, apkTool)
            apkTool.decode(apk, frameworks, tmpDir, force=True)

            for patch in patches:
                self.patchTool.patch(tmpDir, patch, 1)

            apkTool.build(tmpDir, frameworks, dest)

            shutil.rmtree(tmpDir)
        except:
            shutil.rmtree(tmpDir)
            raise


