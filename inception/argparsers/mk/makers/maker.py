import abc
from inception.config.config import ConfigProperty
class Maker(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, config, key):
        self.config = config
        self.key = key

    def getKey(self):
        return self.key

    def getConfig(self):
        return self.config

    def getFSPath(self):
        return self.config.getFSPath()

    def getDeviceConfigValue(self, key, default = None):
        key = "device." + key
        return self.config.get(key, default)

    def getCommonConfigValue(self, key, default = None):
        key = "common." + key
        return self.config.get(key, default)

    def getCommonConfigProperty(self, key, default = None):
        key = "common." + key
        return self.config.getProperty(key, default)

    def getMakeConfigValue(self, key, default = None, directOnly = False):
        res = self.getMakeConfigProperty(key, default, directOnly)
        if res and res.__class__ == ConfigProperty:
                return res.getValue()
        return res

    def getMakeConfigProperty(self, key, default = None, directyOnly = False):
        key = self.getKey() + "." + key
        return self.config.getProperty(key, default, directyOnly)

    def setConfigValue(self, key, value):
        return self.config.set(key, value)

    @abc.abstractmethod
    def make(self, workDir, outDir):
        pass
