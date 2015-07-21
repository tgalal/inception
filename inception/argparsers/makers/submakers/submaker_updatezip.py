from .submaker import Submaker
from inception.tools.signapk import SignApk
import shutil
import os
from inception.constants import InceptionConstants

class UpdatezipSubmaker(Submaker):
    def make(self, updatePkgDir):
        keys_name = self.getValue("keys")
        signingKeys = self.getMaker().getConfig().getKeyConfig(keys_name) if keys_name else None
        updateBinaryKey, updateBinary = self.getTargetBinary("update-binary")
        assert updateBinary, "%s is not set" % updateBinaryKey

        if keys_name:
            assert signingKeys, "update.keys is '%s' but __config__.host.keys.%s is not set" % (keys_name, keys_name)
            signingKeys = signingKeys["private"], signingKeys["public"]

        shutil.copy(updateBinary, os.path.join(updatePkgDir, "META-INF/com/google/android/update-binary"))
        updateZipPath = updatePkgDir + "/../"
        updateZipPath += "update_unsigned" if signingKeys else "update"
        shutil.make_archive(updateZipPath, "zip", updatePkgDir)
        updateZipPath += ".zip"

        if signingKeys:
            javaKey, javaPath = self.getHostBinary("java")
            signApkKey, signApkPath = self.getHostBinary("signapk")

            assert signApkPath, "%s is not set" % signApkKey

            assert os.path.exists(signApkPath), "'%s' from %s does not exist" % (signApkPath, signApkKey)
            assert os.path.exists(javaPath), "'%s' from %s does not exist" % (javaPath, javaKey)

            signApk = SignApk(javaPath, signApkPath)
            targetPath =  updatePkgDir + "/../" + InceptionConstants.OUT_NAME_UPDATE
            signApk.sign(updateZipPath, targetPath, signingKeys[0], signingKeys[1])
            updateZipPath = targetPath

        return updateZipPath


