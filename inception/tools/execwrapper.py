from inception.inceptionobject import InceptionObject
class ExecWrapper(InceptionObject):
    def __init__(self, bin):
        super(ExecWrapper, self).__init__()
        self.bin = bin
        self.preArgs = ()
        self.postArgs = ()
        self.args = {}
        self.shortArgPrefix = "-"
        self.longArgPrefix = "--"
        self.cwd = None
        self.stdin = None

    def setShortArgPrefix(self, prefix):
        self.shortArgPrefix = prefix

    def setLongArgPrefix(self, prefix):
        self.longArgPrefix = prefix

    def setCwd(self, cwd):
        self.cwd = cwd

    def setStdIn(self, f):
        if type(f) is str:
            self.stdin = open(f, "r")
        else:
            self.stdin = f

    def addPreArg(self, preArg):
        if type(preArg) is not tuple:
            preArg = (preArg,)
        self.preArgs += preArg

    def addPostArg(self, postArg):
        if type(postArg) is not tuple:
            postArg = (postArg,)
        self.postArgs += postArg

    def clearArgs(self):
        self.args = {}
        self.preArgs = ()
        self.postArgs = ()

    def setArg(self, arg, value = None):
        self.args[arg] = value

    def createArgs(self):
        args = ()
        for k, v in self.args.items():
            prefix = self.shortArgPrefix if len(k) == 1 else self.longArgPrefix
            args += ("%s%s" % (prefix, k),)
            if v is not None:
                args +=  (v,)

        return self.preArgs + args + self.postArgs

    def run(self, preview = False):
        cmd = tuple(self.bin.split(" ")) + self.createArgs()
        result = self.execCmd(*cmd, cwd = self.cwd, stdin = self.stdin, preview = preview)
        if self.stdin:
            self.stdin.close()
        return result

    def preview(self):
        return self.run(preview = True)
