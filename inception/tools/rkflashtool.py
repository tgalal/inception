from execwrapper import ExecWrapper
import tempfile, os
class RkFlashTool(ExecWrapper):
    def flash(self, **kwargs):
        
        for partition, img in kwargs.items():
            self.clearArgs()
            self.setStdIn(img)
            self.addPreArg("w")
            self.addPostArg(partition)
            self.run()

        self.clearArgs()
        self.addPreArg("w")
        self.addPostArg("0x2020")
        self.addPostArg("0x20")
        fd,path = tempfile.mkstemp()
        f = open(path, "w")
        f.write("boot-recovery")
        f.close()

        self.setStdIn(path)

        self.run()
        os.remove(path)

        self.clearArgs()
        self.addPreArg("b")
        self.setStdIn(None)
        self.run()

        return True