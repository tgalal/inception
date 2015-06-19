import abc
class Submaker(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, maker, key):
        self.maker = maker
        self.key = key

    def getMaker(self):
        return self.maker

    @abc.abstractmethod
    def make(self, workDir, updatescriptgen = None):
        pass

    def newtmpWorkDir(self):
        return self.maker.newTmpWorkDir()

    def getFSPath(self):
        return self.maker.getFSPath()

    def getValue(self, key, default = None, directOnly = False):
        if not self.key == ".":
            key = self.key + "." + key if not key == "." else self.key
        return self.maker.getMakeValue(key, default, directOnly)

    def getProperty(self, key, default = None, directOnly = False):

        if not self.key == ".":
            key = self.key + "." + key if not key == "." else self.key
        return self.maker.getMakeProperty(key, default, directOnly)

    def setValue(self, key, value):
        return self.maker.setValue(key, value)

    def deleteProperty(self, key):
        return self.maker.deleteProperty(key)

    def getHostBinary(self, name):
        return self.maker.getHostBinary(name)

    def getTargetBinary(self, name):
        return self.maker.getTargetBinary(name)

    def getHostBinaryConfigProperty(self, name, default = None, directOnly = False):
        return self.maker.getHostBinaryConfigProperty(name, default, directOnly)

    def getTargetBinaryConfigProperty(self, name, default = None, directOnly = False):
        return self.maker.getTargetBinaryConfigProperty(name, default, directOnly)

    # def getConfigProperty(self, name, default = None, directOnly = False):
    #     return self.maker.getConfigProperty(name, default, directOnly)
    #
    # def getConfigValue(self, name, default = None, directOnly = False):
    #     return self.maker.getConfigValue(name, default ,directOnly)

    def getHostConfigProperty(self, name, default = None, directOnly = False):
        return self.maker.getHostConfigProperty(name, default, directOnly)

    def getHostConfigValue(self, name, default = None, directOnly = False):
        return self.maker.getHostConfigValue(name, default ,directOnly)


    def getTargetConfigProperty(self, name, default = None, directOnly = False):
        return self.maker.getTargetConfigProperty(name, default, directOnly)

    def getTargetConfigValue(self, name, default = None, directOnly = False):
        return self.maker.getTargetConfigValue(name, default ,directOnly)
