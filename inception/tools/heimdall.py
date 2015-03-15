from execwrapper import ExecWrapper
class Heimdall(ExecWrapper):
    def flash(self, **kwargs):
        self.clearArgs()
        self.addPreArg("flash")
        for partition, img in kwargs.items():
            self.setArg(partition, img)

        return self.run()