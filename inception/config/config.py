import json
import os
import re
from inception.constants import InceptionConstants
import sys
import shutil
from inception.argparsers.makers.maker_cache import CacheMaker
from inception.argparsers.makers.maker_update import UpdateMaker
from inception.argparsers.makers.maker_odin import OdinMaker
from inception.argparsers.makers.maker_image_boot import BootImageMaker
from inception.argparsers.makers.maker_image_recovery import RecoveryImageMaker
from inception.argparsers.makers.maker_package import PackageMaker
from inception.argparsers.makers.maker_config import ConfigMaker
from inception.argparsers.makers.maker_extras import ExtrasMaker
from inception.argparsers.makers.maker_installercmd import InstallerCmdMaker
from inception.argparsers.makers.maker_dnx import DnxMaker
import logging

logger = logging.getLogger(__name__)

if sys.version_info >= (3,0):
    unicode = str

PATH_OUT_DNX = "dnx"
PATH_OUT_ODIN = "odin"

class Config(object):
    __OVERRIDE_KEY__ = "__override__"

    TEMPLATE_DEFAULT = {
        "__extends__": None,
        "update": {
            "network": {
                "aps": []
            }
        }
    }

    def __init__(self, identifier, contextData, parent = None, source = None):
        self.identifier = identifier
        self.parent = parent if parent else None
        self.source = source
        self.__contextData = contextData
        self.outPath = None

    @classmethod
    def new(cls, identifier, name = None, base = None, template = None):
        sourceTemplate = template if template is not None else cls.TEMPLATE_DEFAULT
        sourceTemplate = sourceTemplate.copy()

        if base: assert base.__class__ == cls, "Base must be instance of %s, got %s" % (cls, base.__class__)
        config = cls(identifier, sourceTemplate, base)
        if base:
            config.set("__extends__", base.getIdentifier() )
            # config.set("boot.__make__", base.get("boot.__make__", False))
            # config.set("recovery.__make__", base.get("recovery.__make__", False))
            # config.set("cache.__make__", base.get("cache.__make__", False))
            # config.set("odin.__make__", base.get("odin.__make__", False))
            #
            # config.set("update.restore_stock_recovery", base.get("update.restore_stock_recovery", base.get("recovery.stock", None) is not None))
            # config.set("update.settings.__make__", base.get("update.settings.__make__", False))
            # config.set("update.databases.__make__", base.get("update.databases.__make__", False))
            # config.set("update.adb.__make__", base.get("update.adb.__make__", False))
            # config.set("update.apps.__make__", base.get("update.apps.__make__", False))
            # config.set("update.busybox.__make__", base.get("update.busybox.__make__", False))
            # config.set("update.root_method", base.get("update.root_method", None))
            # config.set("update.property.__make__", base.get("update.property.__make__", False))
            # config.set("update.network.__make__", base.get("update.network.__make__", False))
            # config.set("update.keys", base.get("update.keys", None))
            # config.set("update.script.format_data", base.get("update.script.format_data", False))
            config.set("__notes__", base.get("__notes__", [], directOnly=True))

        return config


    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def resolveRelativePath(self, path):
        if path.startswith("/"):
            return path

        return os.path.join(self.getSource(True), path)

    def cloneContext(self):
        return self.__contextData.copy()

    def dumpContextData(self):
        return json.dumps(self.__contextData, indent=4)

    def dumpFullData(self):
        fullConfig = self #Config("__full__", self.cloneContext())
        curr = self
        while not curr.isOrphan():
            curr = curr.getParent()
            currCopy = Config("__full__", curr.cloneContext())
            currCopy.override(fullConfig)
            fullConfig = currCopy

        return fullConfig.dumpContextData()

    def override(self, config):
        for key in config.keys():
            # self.set(key.replace(".", "\."), config.get(key))
            self.set(key, config.get(key))

    def keys(self, dictionary = None):
        dictionary = dictionary or self.__contextData
        keys = []
        for key, item in dictionary.iteritems():
            if type(item) is dict and len(item):
                keys.extend(map(lambda i: key.replace(".", "\.") + "." + i, self.keys(item)))
            else:
                keys.append(key.replace(".", "\."))

        return keys

    def dumpSources(self):
        print(self.getSource())
        if self.parent:
            self.parent.dumpSources()

    def get(self, key, default = None, directOnly = False):
        try:
            result = self.__getProperty(key)
            if type(result) is list:
                override = self.__class__.__OVERRIDE_KEY__ in result
                r = result[:]
                while self.__class__.__OVERRIDE_KEY__ in r:
                    r.remove(self.__class__.__OVERRIDE_KEY__)
                if not override and not directOnly and self.parent:
                    r.extend(self.parent.get(key, []))
                    return r
                result = r
            elif type(result) is dict:
                override = self.__class__.__OVERRIDE_KEY__ in result and result[self.__class__.__OVERRIDE_KEY__] == True
                r = result.copy()
                if self.__class__.__OVERRIDE_KEY__ in r: del r[self.__class__.__OVERRIDE_KEY__]
                if not override and not directOnly and self.parent:
                    # r.update(self.parent.get(key, {}))
                    parentData = self.parent.get(key, {})
                    if type(parentData) is dict:
                        p = Config("__sub__", parentData)
                        p.override(Config("__sub__", r))
                        return p.__contextData
                result = r
            return result
        except ValueError:
            if not directOnly and self.parent and not self.keyOverridesParent(key):
                return self.parent.get(key, default)
        return default

    def getProperty(self, key, default = None, directOnly = False):
        try:
            result = self.__getProperty(key)
            if type(result) in (unicode, str):
                result = result.encode()
            elif type(result) is list:
                override = self.__class__.__OVERRIDE_KEY__ in result
                r = result[:]
                while self.__class__.__OVERRIDE_KEY__ in r:
                    r.remove(self.__class__.__OVERRIDE_KEY__)
                if not override and not directOnly and self.parent:
                    r.extend(self.parent.get(key, []))
                result = r
            elif type(result) is dict:
                override = self.__class__.__OVERRIDE_KEY__ in result and result[self.__class__.__OVERRIDE_KEY__] == True
                r = result.copy()
                if self.__class__.__OVERRIDE_KEY__ in r: del r[self.__class__.__OVERRIDE_KEY__]
                if not override and not directOnly and self.parent:
                    # r.update(self.parent.get(key, {}))
                    parentData = self.getParent().get(key, {})
                    if type(parentData) is dict:
                        p = Config("__sub__", parentData)
                        p.override(Config("__sub__", r))
                        r = p.__contextData
                result = r
            return ConfigProperty(self, key, result)
        except ValueError:
            if not directOnly and self.parent and not self.keyOverridesParent(key):
                return self.parent.getProperty(key, default)
        return ConfigProperty(self, key, default)

    def keyOverridesParent(self, key):
        dissect = re.split(r'(?<!\\)\.', key)
        for i in range(len(dissect), 0, -1):
            keyPart = ".".join([dissect[j] for j in range(0, i)]) + "." + self.__class__.__OVERRIDE_KEY__
            try:
                if self.__getProperty(keyPart) is True:
                    return True
            except ValueError:
                pass

        return False


    def set(self, key, value, diffOnly = False):
        if diffOnly and self.get(key) == value:
            return
        self.__setProperty(key, value)


    def setRecursive(self, key, val):
        if type(val) is dict:
            for k,v in val.items():
                self.setRecursive(key + "." + k, v)
        else:
            self.set(key, val)

    def delete(self, key):
        self.__delProperty(key)

    def __delProperty(self, keys, d):
        d = d if d is not None else self.__contextData
        dissect = re.split(r'(?<!\\)\.', keys, 1)

        if len(dissect) > 1:
            key, rest = dissect
            key = key.replace("\.", ".")
            if key not in d or type(d[key]) is not dict:
                d[key] = {}
            self.__delProperty(rest, d[key])
        else:
            del d[keys.replace("\.", ".")]
            if not self.isOrphan():
                self.getParent().delete(keys)

    def __setProperty(self, keys, item, d = None):
        d = d if d is not None else self.__contextData
        dissect = re.split(r'(?<!\\)\.', keys, 1)

        if len(dissect) > 1:
            key, rest = dissect
            key = key.replace("\.", ".")
            if key not in d or type(d[key]) is not dict:
                d[key] = {}
            self.__setProperty(rest, item, d[key])
        else:
            d[keys.replace("\.", ".")] = item
            #d[keys] = item

    def __getProperty(self, keys, d = None):
        d = d or self.__contextData
        dissect = re.split(r'(?<!\\)\.', keys, 1)
        if len(dissect) > 1:
            key, rest = dissect
            if key.replace("\\", "")  not in d:
                raise ValueError("Property not found")
            return self.__getProperty(rest, d[key.replace("\\", "")])
        elif keys.replace("\\", "") in d:
            return d[keys.replace("\\", "")]
        else:
            raise ValueError("Property not found")

    def getSource(self, getDir = False):
        return os.path.dirname(self.source) if getDir and self.source else self.source

    def getIdentifier(self):
        return self.identifier

    def getFSPath(self):
        return self.resolveRelativePath(InceptionConstants.FS_DIR)
        # return os.path.join(os.path.dirname(self.getSource()), InceptionConstants.FS_DIR)

    def isOrphan(self):
        return self.parent is None

    def getParent(self):
        return self.parent

    def isBase(self):
        return len(self.getIdentifier().split(".")) == 2

    def setOutPath(self, outPath, keepDirs = True):
        self.outPath = outPath

        if not keepDirs:
            self.outPath = outPath
        else:
            a,b,c = self.getIdentifier().split(".")
            self.outPath = os.path.join(outPath, a, b, c)

    def getOutPath(self):
        if self.isBase():
            raise ValueError("Base configs have no out paths: %s "% self.getIdentifier())

        if not self.outPath:
            self.setOutPath(InceptionConstants.OUT_DIR)

        return self.outPath

    def getDnxOutPath(self):
        return self.get("dnx.out", PATH_OUT_DNX)

    def getOdinOutPath(self):
        return self.get("odin.out", PATH_OUT_ODIN)

    def isMakeable(self, key):
        return self.get(key + ".__make__", False)

    def prepareOutDir(self, clearOutPath):
        outDir = self.getOutPath()
        if clearOutPath and os.path.exists(outDir):
            logger.info("Cleaning out dir")
            shutil.rmtree(outDir)

        if not os.path.exists(outDir):
            os.makedirs(outDir)

    def make(self, workDir, clearOutPath = True):
        self.prepareOutDir(clearOutPath)
        makersMap = [
            ("boot", BootImageMaker),
            ("recovery", RecoveryImageMaker),
            ("update", UpdateMaker),
            ("cache", CacheMaker),
            ("extras", ExtrasMaker),
            ("odin", OdinMaker),
            ("config", ConfigMaker),
            ("installercmd", InstallerCmdMaker),
            ("dnx", DnxMaker),
            ("package", PackageMaker)
         ]

        out = {}

        for makerItem in makersMap:
            key, Maker = makerItem
            if self.get(key + ".__make__", Maker.DEFAULT_MAKE):
                logger.info("Making %s" % key)
                m = Maker(self)
                out[key] = m.make(workDir, self.getOutPath())
                logger.info("Made %s" % key)
            else:
                logger.info("Skipping '%s' as it's disabled in config" % key)

        outStr = "Made:\n\n"
        footer = self.get("update.script.footer", None)
        if footer:
            print("\n%s\n" % footer)
        maxLen = max([len(key) for key in out.keys()])
        for k, v in out.items():
            outStr += "%*s %s\n" % (-(maxLen + 5), k, v)
        logger.info(outStr)







class ConfigProperty(object):
    def __init__(self, config, key, value):
        self.key = key
        self.value = value
        self.config = config

    def getKey(self):
        return self.key

    def getValue(self):
        return self.value

    def getConfig(self):
        return self.config

    def resolveAsRelativePath(self):
        return self.resolveRelativePath(self.getValue()) if type(self.getValue()) is str else None

    def resolveRelativePath(self, path):
        return self.getConfig().resolveRelativePath(path)

    def __str__(self):
        return "%s:\t%s" % (self.getKey(), self.getValue())



# class JSONDotIdentifierResolver(DotIdentifierResolver):
#     def resolve(self, identifier):
#         path = super(JSONDotIdentifierResolver, self).resolve(identifier)
#         if path:
#             return os.path.join(path, os.path.basename(path) + ".json")
#
# if __name__ == "__main__":
#     resolver = DotIdentifierResolver()
#     resolver.addLookupPath("/home/tarek/Projects.LinuxOnly/inception.pub/device")
#     resolver.addLookupPath("/home/tarek/Projects.LinuxOnly/inception.pub/base")
#     ctp = ConfigTreeParser(resolver)
#
#     parsed = ctp.parseJSON("trekstor.g30refN79A.test")
#     parsed["aaa.bbb.ccc"] = 5
#     parsed.dumpContextData()
#     parsed.dumpSources()
