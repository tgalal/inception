from .submaker import Submaker
import zipfile
import os
import shutil
import logging

logger = logging.getLogger(__name__ )

class SuperSuSubmaker(Submaker):

    def make(self, workDir):
        supersuZipProp = self.getTargetConfigProperty("root.methods.supersu.path")
        assert supersuZipProp.getValue(), "Must set %s to the supersu zip file" % supersuZipProp.getKey()
        includeApk = self.getTargetConfigValue("root.methods.supersu.include_apk", True)
        includeArchs = set(self.getTargetConfigValue("root.methods.supersu.include_archs", []))

        superSuTargetRelativePath = "supersu"
        supersuTargetPath = os.path.join(workDir, superSuTargetRelativePath)
        postinstFilePath =  os.path.join(supersuTargetPath, "supersu_installer_includer")
        supersuOriginalUpdatescriptPath = os.path.join(supersuTargetPath, "supersu_installer.sh")
        newSuperSuZipPath = os.path.join(supersuTargetPath, "supersu.zip")
        superSuZipTmpExtract = "/tmp/supersu.zip"
        superSuUpdatescriptTmpExtract = "/tmp/supersu_installer.sh"
        superuserApkPath = os.path.join("common", "Superuser.apk")

        with self.newtmpWorkDir() as tmpDir:
            with zipfile.ZipFile(supersuZipProp.resolveAsRelativePath(), "r") as z:
                z.extractall(tmpDir)
                os.mkdir(os.path.join(workDir, "supersu"))
                archs = set(
                    [f for f in os.listdir(tmpDir) if not f in ("common", "META-INF")]
                )

                unsupportedArchs = includeArchs.difference(archs)
                if len(unsupportedArchs):
                    unsupportedArchs = list(unsupportedArchs)
                    raise ValueError("Can't find archs: [%s] in supersu" % (", ".join(unsupportedArchs)))

                targetArchs = includeArchs if len(includeArchs) else archs

                newSuperSuZip = zipfile.ZipFile(newSuperSuZipPath, "w")

                for arch in targetArchs:
                    self.__addDirToZip(newSuperSuZip, os.path.join(tmpDir, arch), arch)

                if not includeApk:
                    os.remove(os.path.join(tmpDir, superuserApkPath))
                self.__addDirToZip(newSuperSuZip, os.path.join(tmpDir, "common"), "common")


                if self.getMaker().getConfig().isMakeable("update.busybox"):
                    #process file, with busybox onboard in assumption
                    with open(os.path.join(tmpDir, "META-INF/com/google/android/update-binary"), "r") as f:
                        with open(supersuOriginalUpdatescriptPath, "w") as targetF:
                            for l in f.readlines():
                                if l.startswith("#!"):
                                    targetF.write("#!" + self.getTargetConfigValue("root.methods.supersu.sh", "/system/bin/sh") + "\n")
                                else:
                                    targetF.write(l)
                else:
                    shutil.copy(os.path.join(tmpDir, "META-INF/com/google/android/update-binary"), supersuOriginalUpdatescriptPath)

                postInstscript = "ui_print(\"Installing SuperSU..\");\n"
                postInstscript += "run_program(\"%s\", \"1\", \"stdout\", \"%s\");" % (superSuUpdatescriptTmpExtract, superSuZipTmpExtract)

                with open(postinstFilePath, "w") as postinstFile:
                    postinstFile.write(postInstscript)

                superSuConfig = supersuZipProp.getConfig()
                currPostInst = superSuConfig.get("script.post", [], directOnly=True)
                currPostInst.append(postinstFilePath)
                superSuConfig.set("update.script.post", currPostInst)

        self.setValue("update.files.add." + newSuperSuZipPath.replace(workDir, "").replace(".", "\.") , {
            "destination": superSuZipTmpExtract
        })

        self.setValue("update.files.add." + supersuOriginalUpdatescriptPath.replace(workDir, "").replace(".", "\."), {
            "destination": superSuUpdatescriptTmpExtract,
            "mode": "0755",
            "uid": "0",
            "gid": "0"
        })

    def __addDirToZip(self, zipFile, dirPath, zipRoot):
        zipFile.write(dirPath, zipRoot)
        for f in os.listdir(dirPath):
            src = os.path.join(dirPath, f)
            dest = os.path.join(zipRoot, f)

            if os.path.isdir(src):
                self.__addDirToZip(zipFile, src, dest)
            else:
                zipFile.write(src, dest)
