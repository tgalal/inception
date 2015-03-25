import abc
class Submaker(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, maker, key):
        self.maker = maker
        self.key = key

    def getMaker(self):
        return self.maker

    @abc.abstractmethod
    def make(self, workDir):
        pass

    def getFSPath(self):
        return self.maker.getFSPath()

    def getConfigValue(self, key, default = None, directOnly = False):
        return self.maker.getMakeConfigValue(self.key + "." + key, default, directOnly)

    def getConfigProperty(self, key, default = None, directyOnly = False):
        return self.maker.getMakeConfigProperty(self.key + "." + key, default, directyOnly)

    def setConfigValue(self, key, value):
        return self.maker.setConfigValue(key, value)