from constants import InceptionConstants
from inception import InceptionObject
import os, json, sys
class ConfigNotFoundException(Exception):
    pass
class ConfigNotValidException(Exception):
    pass


class Config(object):
    def __init__(self, data, path, identifier, full = False):
        self.path = path
        self.data = data
        self.identifier = identifier
        self.full = full;


    def isFull(self):
        return self.full

    def toString(self):
        return json.dumps(self.getData(),  indent = 4, separators=(',', ': '))

    def getIdentifier(self):
        return self.identifier

    def getData(self):
        return self.data

    def getPath(self):
        return self.path

    def getFSPath(self):
        return os.path.join(os.path.dirname(self.getPath()), InceptionConstants.FS_DIR)

    def getParent(self):
        if "extends" in self.data and self.data["extends"] is not None:
            _,_, p = Configurator.findConfig(self.data["extends"])
            data = Configurator.parseConfig(p)
            return Config(data, p, self.data["extends"])
        return None

    def isOrphan(self):
        return "extends" not in self.data or self.data["extends"] is None

    def setProperty(self, keys, item, d = None):
        d = d or self.data
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                d[key] = {}
            self.setProperty(rest, item, d[key])
        else:
            d[keys] = item

    def getProperty(self, keys, d = None):
        d = d or self.data
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                raise ValueError("Property not found")
            return self.getProperty(rest, d[key])
        elif keys in d:
            return d[keys]
        else:
            raise ValueError("Property not found")

    def set(self, keys, item):
        return self.setProperty(keys, item)

    def get(self, prop, default = None):
        try:
            result = self.getProperty(prop)
            return result or default
        except ValueError, e:
            if not self.isOrphan() and not self.isFull():
                parent = self.getParent()
                if parent is not None:
                    return parent.get(prop, default)

            return default



class Configurator(InceptionObject):

    def __init__(self, identifier):
        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR

        self.identifier = identifier
        config = Configurator.findConfig(identifier)
        if config is None:
            raise ConfigNotFoundException("Couldn't find config for %s" % identifier)

        self.vendor, self.model, self.configPath = config

        self.configTree = self.fetchConfigTree(identifier)

        self.config = Config(self.createConfigFromTree(self.configTree), self.configPath, self.identifier, full = True)

    def getConfigTree(self):
        return self.configTree

    def getConfigModel(self):
        return self.model

    def getConfigVendor(self):
        return self.vendor

    def getConfigPath(self):
        return self.configPath

    def getConfigIdentifier(self):
        return self.identifier

    def getConfig(self):
        return self.config



    def createConfigTemplate(self, name, baseConfig = None):

        config = {
            "extends": baseConfig.getIdentifier() if baseConfig is not None else None,
            "device": {
                "__extend__": True,
                "name":  name
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


        return Config(config, None, None, full = False)

    def createConfigFromTree(self, configTree):
        if len(configTree) == 1:
            return configTree[0]
        if len(configTree) == 2:
            return self.mergeConfigTrees(configTree[0], configTree[1])

        return self.createConfigFromTree([self.mergeConfigTrees(configTree[0], configTree[1])] + configTree[2:])

    def mergeConfigTrees(self, ct1, ct2):
        return self.combineConfigs(ct1, ct2)


    def combineConfigs(self, dictionary1, dictionary2):
        combineDicts = self.combineConfigs 
        output = {}
        for item, value in dictionary1.iteritems():
            if dictionary2.has_key(item):
                if isinstance(dictionary2[item], dict) and (("__extend__" not in dictionary2[item]) or dictionary2[item]["__extend__"] == True):
                    output[item] = combineDicts(value, dictionary2.pop(item))
                elif isinstance(dictionary2[item], list):
                    output[item] = dictionary2.pop(item) + value
            else:
                output[item] = value
        for item, value in dictionary2.iteritems():
             output[item] = value
        return output


    def fetchConfigTree(self, identifier):
        config = Configurator.findConfig(identifier)
        if config is None:
            raise ConfigNotFoundException(identifier)

        vendor, model, configPath = config
        config = self.parseConfig(configPath)
        configTree = [config]
        if "extends" in config and config["extends"] is not None:
            return self.fetchConfigTree(config["extends"]) + configTree
        else:
            return configTree     
    @staticmethod
    def parseConfig(configPath):
        jsonFile = open(configPath)
        jsonObj = json.load(jsonFile)
        jsonFile.close()
        if "files" in jsonObj and type(jsonObj["files"]) is dict and  "__comment__" in jsonObj["files"]:
            del jsonObj["files"]["__comment__"]
        return jsonObj

    @staticmethod
    def findConfig(configName):
        #look inside device for specified id
        #return if found else:
        #look inside base
        #return if found else:
        #error
        vendor = None
        model = None
        variant = None


        deviceDir = InceptionConstants.VARIANTS_DIR
        baseDir = InceptionConstants.BASE_DIR
        d = Configurator.sd

        nsplit = configName.split('.')
        if len(nsplit) == 3:
            vendor, model, configName = nsplit
            path = os.path.join(deviceDir, vendor, model, configName, "%s.json" % configName)
            return (vendor, model, path) if os.path.exists(path) else None
            #will look only under device
        elif len(nsplit) == 2:
            vendor, configName = nsplit
            path = os.path.join(baseDir, vendor, configName, "%s.json" % configName)
            return (vendor, configName, path)if os.path.exists(path) else None
        else:
            d("Looking for", configName, "in", deviceDir)
            vendors = os.listdir(deviceDir)
            for v in vendors:
                modelsDir = os.path.join(deviceDir, v)
                models = os.listdir(modelsDir)
                d("Entering", modelsDir)
                for m in models:
                    variantsDir = os.path.join(modelsDir, m)
                    variants = os.listdir(variantsDir)

                    configPath = os.path.join(variantsDir, configName, "%s.json" % configName)
                    d("Checking", configPath)
                    if os.path.exists(configPath):
                        return (v, m, configPath)

            d("Looking for", configName, "in", baseDir)
            vendors = os.listdir(baseDir)
            for v in vendors:
                modelsDir = os.path.join(baseDir, v)
                models = os.listdir(modelsDir)
                configPath = os.path.join(modelsDir, configName, "%s.json" % configName)
                d("Checking", configPath)
                if os.path.exists(configPath):
                    return (v, configName, configPath)

    @staticmethod
    def sd(*messages):
        print("%s:\t%s" % ("Configurator", "\t".join(messages) ))
    def d(self, *messages):
        print("%s:\t%s" % (self.__class__.__name__, "\t".join(messages) ))
