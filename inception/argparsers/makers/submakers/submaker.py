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

    def getCommonValue(self, key, default = None):
        return self.getMaker().getCommonValue(key, default)

    def getCommonProperty(self, key, default = None):
        return self.getMaker().getCommonProperty(key, default)

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