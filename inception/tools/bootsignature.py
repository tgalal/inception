from .execwrapper import ExecWrapper
class BootSignature(ExecWrapper):
    def __init__(self, javaBin, bootSignatureJar):
        super(BootSignature, self).__init__(javaBin)
        self.bootSignatureBin = bootSignatureJar
        self.setLongArgPrefix("-")

    def sign(self, targetName, src, privateKeyPath, publicKeyPath, dest):
        self.clearArgs()
        self.setArg("jar", self.bootSignatureBin)
        self.addPostArg(targetName)
        self.addPostArg(src)
        self.addPostArg(privateKeyPath)
        self.addPostArg(publicKeyPath)
        self.addPostArg(dest)
        self.run()