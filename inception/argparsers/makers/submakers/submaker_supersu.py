from .submaker import Submaker
import zipfile
import os
import shutil

class SuperSuSubmaker(Submaker):

    def make(self, workDir):
        supersuZipProp = self.getCommonConfigProperty("root.methods.supersu.path")
        assert supersuZipProp.getValue(), "Must set root.methods.supersu.path to the supersu zip file"
        includeApk = self.getCommonConfigValue("root.methods.supersu.include_apk", True)
        includeArchs = set(self.getCommonConfigValue("root.methods.supersu.include_archs", []))

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

                shutil.copy(os.path.join(tmpDir, "META-INF/com/google/android/update-binary"), supersuOriginalUpdatescriptPath)

                postInstscript = "ui_print(\"Installing SuperSU..\");\n"
                postInstscript += "run_program(\"%s\", \"1\", \"stdout\", \"/tmp/supersu.zip\");" % (superSuUpdatescriptTmpExtract)

                with open(postinstFilePath, "w") as postinstFile:
                    postinstFile.write(postInstscript)

                currPostInst = self.getMaker().getConfig().get("script.post", [], directOnly=True)
                currPostInst.append(postinstFilePath)
                self.setConfigValue("update.script.post", currPostInst)

        self.setConfigValue("update.files.add." + newSuperSuZipPath.replace(workDir, "").replace(".", "\.") , {
            "destination": superSuZipTmpExtract
        })

        self.setConfigValue("update.files.add." + supersuOriginalUpdatescriptPath.replace(workDir, "").replace(".", "\."), {
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
