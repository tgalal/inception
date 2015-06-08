from .submaker import Submaker
from inception.tools.signapk import SignApk
import shutil
import os
from inception.constants import InceptionConstants
class UpdatezipSubmaker(Submaker):
    def make(self, updatePkgDir):
        signingKeys = None
        keys_name = self.getConfigValue("keys")
        updateBinaryProp = self.getCommonConfigProperty("tools.update-binary.bin")
        assert updateBinaryProp.getValue(), "common.tools.update-binary.bin is not set"
        updateBinary = updateBinaryProp.getConfig().resolveRelativePath(updateBinaryProp.getValue())

        if keys_name:
            signingKeysProp= self.getCommonConfigProperty("tools.signapk.keys.%s" % keys_name)
            if(signingKeysProp):
                pub = signingKeysProp.getValue()["public"]
                priv = signingKeysProp.getValue()["private"]
                pubPath = signingKeysProp.getConfig().resolveRelativePath(pub)
                privPath =signingKeysProp.getConfig().resolveRelativePath(priv)
                signingKeys = privPath, pubPath

        shutil.copy(updateBinary, os.path.join(updatePkgDir, "META-INF/com/google/android/"))
        updateZipPath = updatePkgDir + "/../"
        updateZipPath += "update_unsigned" if signingKeys else "update"
        shutil.make_archive(updateZipPath, "zip", updatePkgDir)
        updateZipPath += ".zip"

        if signingKeys:
            javaPath = self.getCommonConfigValue("tools.java.bin")
            signApkPathProp = self.getCommonConfigProperty("tools.signapk.bin")

            assert signApkPathProp.getValue(), "common.tools.signapk.bin is not set"

            signApkPath = signApkPathProp.getConfig().resolveRelativePath(signApkPathProp.getValue())


            assert os.path.exists(signApkPath), "'%s' from common.tools.signapk.bin does not exist %s" % signApkPath
            assert os.path.exists(javaPath), "'%s' from common.tools.java.bin does not exist %s" % javaPath


            signApk = SignApk(javaPath, signApkPath)
            targetPath =  updatePkgDir + "/../" + InceptionConstants.OUT_NAME_UPDATE
            signApk.sign(updateZipPath, targetPath, signingKeys[0], signingKeys[1])
            updateZipPath = targetPath

        return updateZipPath


