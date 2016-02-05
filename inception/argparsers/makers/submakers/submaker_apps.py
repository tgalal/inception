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
        apps = self.getValue(".", {})
        if "__make__" in apps:
            del apps["__make__"]
        if "__depend__" in apps:
            del apps["__depend__"]
        for pkgName, data in apps.items():
            apkPath = self.getProperty(pkgName.replace(".", "\.") + ".apk").resolveAsRelativePath()
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


            if "destination" in data:
                destination = data["destination"]
                targetDest = destination[1:] if destination[0] == "/" else destination
                if not targetDest.lower().endswith(".apk"):
                    targetDest = os.path.join(targetDest, os.path.basename(apkPath))
            elif "system" in data and data["system"]:
                targetDest = os.path.join("system/app", os.path.basename(apkPath))
            else:
                targetDest = os.path.join("data/app", os.path.basename(apkPath))

            localDest = os.path.join(workDir, targetDest)

            if not os.path.exists(os.path.dirname(localDest)):
                os.makedirs(os.path.dirname(localDest))

            if len(patchesList):
                if not self.patchTools:
                    key, apkTool = self.getHostBinary("apktool")
                    assert apkTool, "Can't patch APK without apktool. Please set %s" % apkTool
                    frameworks = self.getHostBinaryConfigProperty("apktool.frameworks_dir", None).resolveAsRelativePath()
                    assert frameworks, "Can't patch APK without __config__.host.apktool.frameworks_dir set. " \
                                                  "See http://ibotpeaches.github.io/Apktool/documentation/#frameworks"

                    javakey, java = self.getHostBinary("java")
                    assert java, "Can't use apktool without java. Please set %s" % javakey
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
        self.setValue("update.files.add.%s" % (path.replace(".", "\.")), {
        "destination": "/" + path,
        "gid": "1000",
        "uid": "1000",
        "mode": "0644"
        })

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
