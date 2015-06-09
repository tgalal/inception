from .ext4fs import Ext4FSGenerator
import os, shutil
class CacheImgGenerator(Ext4FSGenerator):
    def __init__(self, workingDir, ext4fsBin):
        super(CacheImgGenerator, self).__init__(ext4fsBin)
        self.setSparsed(True)
        self.workingDir = workingDir
        self.commands = []
        self.recoveryDir = os.path.join(self.workingDir, "recovery")
        if not os.path.exists(self.recoveryDir):
            os.makedirs(self.recoveryDir)

    def _addCommand(self, command):
        self.commands.append(command)

    def update(self, package):
        shutil.copy(package, self.workingDir)
        self._addCommand("--update_package=/cache/%s" % os.path.basename(package))

    def wipeCache(self):
        self.commands.append("--wipe-cache")

    def addFile(self, src, dest = None):
        dest = self.workingDir + dest if dest else self.workingDir

        if os.path.isdir(src):
            shutil.copytree(src, dest + "/" + os.path.basename(src))
        else:
            shutil.copy(src, dest)

    def generate(self, out, adbBinPath = None):
        #write command
        if len(self.commands):
            commandFile = open(self.recoveryDir + "/command", "w")
            commandFile.write("\n".join(self.commands))
            commandFile.close()
        
        super(CacheImgGenerator, self).generate(self.workingDir, out, adbBinPath)