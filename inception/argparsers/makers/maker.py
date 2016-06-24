from inception.constants import InceptionConstants
import abc
import tempfile
import os
import shutil
class Maker(object):
    __metaclass__ = abc.ABCMeta
    DEFAULT_MAKE = True
    def __init__(self, config, key):
        self.config = config
        self.key = key

    def getKey(self):
        return self.key

    def getConfig(self):
        return self.config

    def getFSPath(self):
        return self.config.getFSPath()

    def getDeviceValue(self, key, default = None):
        key = "device." + key
        return self.config.get(key, default)

    def getMakeValue(self, key, default = None, directOnly = False):
        res = self.config.get(self.getKey() + "." + key, default, directOnly)
        return res

    def getMakeProperty(self, key, default = None, directOnly = False):
        key = self.getKey() + "." + key
        return self.config.getProperty(key, default, directOnly)

    def setValue(self, key, value, diffOnly = False):
        return self.config.set(key, value, diffOnly = diffOnly)

    def setHostConfigValue(self, key, value, diffOnly = False):
        return self.config.setHostConfigValue(key, value, diffOnly=diffOnly)

    def setTargetConfigValue(self, key, value, diffOnly = False):
        return self.config.setTargetConfigValue(key, value, diffOnly=diffOnly)

    def deleteProperty(self, key):
        return self.config.delete(key)

    def getCacheOutName(self):
        return self.config.get("cache.out", InceptionConstants.OUT_NAME_CACHE)

    def getHostBinary(self, name):
        return self.config.getHostBinary(name)

    def getTargetBinary(self, name):
        return self.config.getTargetBinary(name)

    def getHostBinaryConfigProperty(self, name, default = None, directOnly = False):
        return self.config.getHostBinaryConfigProperty(name, default, directOnly)

    def getTargetBinaryConfigProperty(self, name, default = None, directOnly = False):
        return self.config.getTargetBinaryConfigProperty(name, default = default, directOnly = directOnly)

    # def getConfigValue(self, name, default = None, directOnly = False):
    #     return self.getConfigProperty(name, default, directOnly).getValue()
    #
    # def getConfigProperty(self, name, default = None, directOnly = False):
    #     return self.config.getConfigProperty(name, default, directOnly)

    def getHostConfigValue(self, name, default = None, directOnly = False):
        return self.getHostConfigProperty(name, default, directOnly).getValue()

    def getHostConfigProperty(self, name, default = None, directOnly = False):
        return self.config.getHostConfigProperty(name, default, directOnly)

    def getTargetConfigValue(self, name, default = None, directOnly = False):
        return self.getTargetConfigProperty(name, default, directOnly).getValue()

    def getTargetConfigProperty(self, name, default = None, directOnly = False):
        return self.config.getTargetConfigProperty(name, default, directOnly)


    def newTmpWorkDir(self):
        return TmpWorkDir()

    @abc.abstractmethod
    def make(self, workDir, outDir):
        pass


class TmpWorkDir(object):
    def __enter__(self):
        self.__path = tempfile.mkdtemp()
        return self.__path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.__path):
            shutil.rmtree(self.__path)
