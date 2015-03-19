import json
import os
from inception.constants import InceptionConstants
class Config(object):

    TEMPLATE_DEFAULT = {
        "extends": None,
        "device": {
            "__extend__": True,
            "name":  None
        },
        "network": {
            "aps": []
        },
        "config": {
            "boot": {
                "kernel": None,
                "ramdisk": None,
            },
            "recovery": {
                "kernel": None,
                "ramdisk": None,
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
        config.set("extends", base.getIdentifier() if base else None)

        return config


    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def cloneContext(self):
        return self.__contextData.copy()

    def dumpContextData(self):
        return json.dumps(self.__contextData, indent=4)

    def dumpFullData(self):
        fullConfig = Config("__full__", self.cloneContext())
        curr = self
        while not curr.isOrphan():
            curr = curr.getParent()
            currCopy = Config("__full__", curr.cloneContext())
            currCopy.override(fullConfig)
            fullConfig = currCopy

        return fullConfig.dumpContextData()

    def override(self, config):
        for key in config.keys():
            self.set(key, config.get(key))

    def keys(self, dictionary = None):
        dictionary = dictionary or self.__contextData
        keys = []
        for key, item in dictionary.iteritems():
            if type(item) is dict and len(item):
                keys.extend(map(lambda i: key + "." + i, self.keys(item)))
            else:
                keys.append(key)

        return keys

    def dumpSources(self):
        print(self.getSource())
        if self.parent:
            self.parent.dumpSources()

    def get(self, key, default = None):
        try:
            result = self.__getProperty(key)
            return result
        except ValueError:
            if self.parent:
                return self.parent.get(key, default)
        return default


    def getProperty(self, key, default = None):
        try:
            result = self.__getProperty(key)
            return ConfigProperty(self, key, result)
        except ValueError:
            if self.parent:
                return self.parent.getProperty(key, default)
        return default


    def set(self, key, value):
        self.__setProperty(key, value)

    def __setProperty(self, keys, item, d = None):
        d = d if d is not None else self.__contextData
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                d[key] = {}
            self.__setProperty(rest, item, d[key])
        else:
            d[keys] = item

    def __getProperty(self, keys, d = None):
        d = d or self.__contextData
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                raise ValueError("Property not found")
            return self.__getProperty(rest, d[key])
        elif keys in d:
            return d[keys]
        else:
            raise ValueError("Property not found")

    def getSource(self, getDir = False):
        return os.path.dirname(self.source) if getDir and self.source else self.source

    def getIdentifier(self):
        return self.identifier

    def getFSPath(self):
        return os.path.join(os.path.dirname(self.getSource()), InceptionConstants.FS_DIR)

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
