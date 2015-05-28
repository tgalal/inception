import json
import os
import re
from inception.constants import InceptionConstants
import sys

if sys.version_info >= (3,0):
    unicode = str


class Config(object):
    __OVERRIDE_KEY__ = "__override__"

    TEMPLATE_DEFAULT = {
        "__extends__": None,
        "device": {
            "name":  None
        },
        "update": {
            "make": True,
            "keys": None,
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

    @classmethod
    def new(cls, identifier, name = None, base = None, template = None):
        sourceTemplate = template if template is not None else cls.TEMPLATE_DEFAULT
        sourceTemplate = sourceTemplate.copy()
        assert base.__class__ == Config, "Base must be instance of config"
        config = Config(identifier, sourceTemplate, base)
        config.set("device.name", name)
        config.set("__extends__", base.getIdentifier() if base else None)

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

    def set(self, key, value):
        self.__setProperty(key, value)

    def c__setProperty(self, keys, item, d = None):
        d = d if d is not None else self.__contextData
        if "." in keys and not keys == ".":
            key, rest = keys.split(".", 1)
            if key not in d or type(d[key]) is not dict:
                d[key] = {}
            self.__setProperty(rest, item, d[key])
        else:
            d[keys] = item

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
        return self.getConfig().resolveRelativePath(self.getValue()) if type(self.getValue()) is str else None

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
