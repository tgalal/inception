from .execwrapper import ExecWrapper
class SignApk(ExecWrapper):
    def __init__(self, javaBin, signApkJar):
        super(SignApk, self).__init__(javaBin)
        self.signApkJar = signApkJar
        self.setLongArgPrefix("-")

    def sign(self, src, dest, privateKeyPath, publicKeyPath):
        self.clearArgs()
        self.setArg("jar", self.signApkJar)
        self.addPostArg("-w")
        self.addPostArg(publicKeyPath)
        self.addPostArg(privateKeyPath)
        self.addPostArg(src)
        self.addPostArg(dest)
        self.run()
