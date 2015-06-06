import abc
import tempfile
import shutil
import os
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
        return TmpWorkDir()

    def getFSPath(self):
        return self.maker.getFSPath()

    def getCommonConfigValue(self, key, default = None):
        return self.getMaker().getCommonConfigValue(key, default)

    def getCommonConfigProperty(self, key, default = None):
        return self.getMaker().getCommonConfigProperty(key, default)

    def getConfigValue(self, key, default = None, directOnly = False):
        if not self.key == ".":
            key = self.key + "." + key if not key == "." else self.key
        return self.maker.getMakeConfigValue(key, default, directOnly)

    def getConfigProperty(self, key, default = None, directOnly = False):

        if not self.key == ".":
            key = self.key + "." + key if not key == "." else self.key
        return self.maker.getMakeConfigProperty(key, default, directOnly)

    def setConfigValue(self, key, value):
        return self.maker.setConfigValue(key, value)

    def deleteConfigProperty(self, key):
        return self.maker.deleteConfigProperty(key)

class TmpWorkDir(object):
    def __enter__(self):
        self.__path = tempfile.mkdtemp()
        return self.__path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.__path):
            shutil.rmtree(self.__path)