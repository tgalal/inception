import abc
from inception.constants import InceptionConstants
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
        res = self.config.get(self.getKey() + "." + key, default, directOnly)
        return res

    def getMakeConfigProperty(self, key, default = None, directyOnly = False):
        key = self.getKey() + "." + key
        return self.config.getProperty(key, default, directyOnly)

    def setConfigValue(self, key, value):
        return self.config.set(key, value)

    def deleteConfigProperty(self, key):
        return self.config.delete(key)

    def getCacheOutName(self):
        return self.config.get("cache.out", InceptionConstants.OUT_NAME_CACHE)

    @abc.abstractmethod
    def make(self, workDir, outDir):
        pass
