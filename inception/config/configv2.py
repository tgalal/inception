from inception.config.config import Config
import platform
import logging
logger = logging.getLogger(__name__)
class ConfigV2(Config):
    KEY_CONFIG          = "__config__"
    KEY_CONFIG_MOUNT    = "mount"
    KEY_CONFIG_HOST     = "host"
    KEY_CONFIG_TARGET   = "target"
    KEY_CONFIG_KEYS     = KEY_CONFIG_HOST + ".keys"
    ARCHS = ["x86", "x86_64", "arm"]
    def __init__(self, *args, **kwargs):
        super(ConfigV2, self).__init__(*args, **kwargs)
        self.hostArch = self.getHostConfigValue("arch")
        if not self.hostArch:
            self.hostArch = platform.machine()

        assert self.hostArch in self.__class__.ARCHS, \
            "Must set %s to one of %s, instead got '%s'" % (self.__class__.KEY_CONFIG + ".host.arch", self.__class__.ARCHS, self.hostArch)

        # if not self.hostArch == platform.machine():
        #     logger.warning("%s is set to %s, while current machine architecture is detected to be %s" %
        #                    (".".join([self.__class__.KEY_CONFIG, self.__class__.KEY_CONFIG_HOST, "arch"]), self.hostArch, platform.machine()))


    def getTargetArch(self):
        targetArch = self.getTargetConfigValue("arch", "any")
        if targetArch != "any":
            assert targetArch and targetArch in self.__class__.ARCHS,\
                "Must set %s to one of %s, instead got '%s'" % (self.__class__.KEY_CONFIG + ".target.arch", self.__class__.ARCHS, targetArch)

        return targetArch


    def setConfigValue(self, name, value, diffOnly = False):
        self.set(self.__class__.KEY_CONFIG + "." + name, value, diffOnly=diffOnly)

    def setHostConfigValue(self, name, value, diffOnly = False):
        self.setConfigValue(self.__class__.KEY_CONFIG_HOST + "." + name, value, diffOnly=diffOnly)

    def setTargetConfigValue(self, name, value, diffOnly = False):
        self.setConfigValue(self.__class__.KEY_CONFIG_TARGET + "." + name, value, diffOnly=diffOnly)

    def getTargetBinaryConfigProperty(self, name, default = None, directOnly = False):
        binKey = "bin." + name
        return self.getTargetConfigProperty(binKey, default, directOnly)

    def getTargetBinary(self, name):
        binKey = "bin.{name}.arch.{arch}"
        key = binKey.format(name=name, arch = self.getTargetArch())
        result = self.getTargetConfigProperty(key)
        if not result.getValue():
            result = self.getTargetConfigProperty(binKey.format(name = name, arch = "any"))

        return (".".join([self.__class__.KEY_CONFIG, self.__class__.KEY_CONFIG_TARGET, key]),
                result.resolveAsRelativePath())

    def getHostBinaryConfigProperty(self, name, default = None, directOnly = False):
        binKey = "bin." + name
        return self.getHostConfigProperty(binKey,default, directOnly)

    def getHostBinary(self, name):
        binKey = "bin.{name}.arch.{arch}"
        key = binKey.format(name=name, arch = self.hostArch)
        result = self.getHostConfigProperty(key)
        if not result.getValue():
            result = self.getHostConfigProperty(binKey.format(name = name, arch = "any"))

        return (".".join([self.__class__.KEY_CONFIG, self.__class__.KEY_CONFIG_HOST, key])
                , result.resolveAsRelativePath())

    def getMountConfig(self, name, default = None):
        if name == "data":
            name = "userdata"

        key = self.__class__.KEY_CONFIG_MOUNT + "." + name
        return self.getTargetConfigValue(key, default)

    def getKeyConfig(self, name):
        keyKey = self.__class__.KEY_CONFIG_KEYS + "." + name
        key = self.getConfigValue(keyKey, None)
        if key is None:
            return None

        public = self.getConfigProperty(keyKey + ".public").resolveAsRelativePath()
        private = self.getConfigProperty(keyKey + ".private").resolveAsRelativePath()

        if public is None:
            raise ValueError("%s.public is not set" % keyKey )

        if private is None:
            raise ValueError("%s.private is not set" % keyKey)

        key["public"] = public
        key["private"] = private

        return key

    def getKeysConfig(self):
        result = {}
        keys = self.getConfigValue(self.__class__.KEY_CONFIG_KEYS, {})
        for keyname in keys.keys():
            result.update(self.getKeyConfig(keyname))

        return result

    def getHostConfigValue(self, key, default = None, directOnly = False):
        return self.getHostConfigProperty(key, default, directOnly).getValue()

    def getHostConfigProperty(self, key, default = None, directOnly = False):
        return self.getConfigProperty(self.__class__.KEY_CONFIG_HOST + "." + key, default, directOnly)

    def getTargetConfigValue(self, key, default = None, directOnly = False):
        return self.getTargetConfigProperty(key, default, directOnly).getValue()

    def getTargetConfigProperty(self, key, default = None, directOnly = False):
        return self.getConfigProperty(self.__class__.KEY_CONFIG_TARGET + "." + key, default, directOnly)

    def getConfigProperty(self, key, default = None, directOnly = False):
        return self.getProperty(self.__class__.KEY_CONFIG + "." + key, default = default, directOnly=directOnly)

    def getConfigValue(self, key, default = None, directOnly = False):
        return self.getConfigProperty(key, default, directOnly).getValue()