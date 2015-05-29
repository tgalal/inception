from .execwrapper import ExecWrapper
class ApkTool(ExecWrapper):
    def __init__(self, javaBin, apkToolJar):
        super(ApkTool, self).__init__(javaBin + " -jar %s" % apkToolJar)
        self.setLongArgPrefix("--")

    def decode(self, apk, frameworksDir, dest, force = False):
        self.clearArgs()
        self.addPreArg("decode")
        self.setArg("frame-path", frameworksDir)
        self.setArg("output", dest)
        if force:
            self.addPostArg("--force")
        self.addPostArg(apk)
        self.run()

    def build(self, path, frameworksDir, dest, originalManifest = True):
        self.clearArgs()
        self.addPreArg("build")
        if originalManifest:
            self.addPreArg("-c")
        self.setArg("frame-path", frameworksDir)
        self.setArg("output", dest)
        self.addPostArg(path)
        self.run()
