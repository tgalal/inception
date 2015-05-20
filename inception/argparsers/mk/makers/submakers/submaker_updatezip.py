from .submaker import Submaker
from inception.tools import SignApk
import shutil
class UpdatezipSubmaker(Submaker):
    def make(self, updatePkgDir):
        signingKeys = None
        keys_name = self.getConfigValue("keys")
        if keys_name:
            signingKeysProp= self.getCommonConfigProperty("tools.signapk.keys.%s" % keys_name)
            if(signingKeysProp):
                pub = signingKeysProp.getValue()["public"]
                priv = signingKeysProp.getValue()["private"]
                pubPath = signingKeysProp.getConfig().resolveRelativePath(pub)
                privPath =signingKeysProp.getConfig().resolveRelativePath(priv)
                signingKeys = privPath, pubPath


        updateZipPath = updatePkgDir + "/../"
        updateZipPath += "update_unsigned" if signingKeys else "update"
        shutil.make_archive(updateZipPath, "zip", updatePkgDir)
        updateZipPath += ".zip"

        if signingKeys:
            javaPath = self.getCommonConfigValue("tools.java.bin")
            signApkPath = self.getCommonConfigValue("tools.signapk.bin")
            signApk = SignApk(javaPath, signApkPath)
            targetPath =  updatePkgDir + "/../update.zip"
            signApk.sign(updateZipPath, targetPath, signingKeys[0], signingKeys[1])
            updateZipPath = targetPath

        return updateZipPath


