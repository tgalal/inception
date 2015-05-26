from .argparser import InceptionArgParser
from inception.constants import InceptionConstants
from inception.config import configtreeparser
import json
from inception.generators.settings import SettingsDatabaseFactory
from inception.config.dotidentifierresolver import DotIdentifierResolver
import logging
import os
import tempfile
logger = logging.getLogger(__name__)

class LearnArgParser(InceptionArgParser):

    def __init__(self):
        super(LearnArgParser, self).__init__(description = "Learn mode cmd")

        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = configtreeparser.ConfigTreeParser(identifierResolver)
        self.tmpDir = tempfile.mkdtemp()

    def process(self):
        super(LearnArgParser, self).process()
        resultDict = {
            "update": {}
        }

        self.config = self.configTreeParser.parseJSON(self.args["variant"])
        resultDict["update"]["settings"] = self.learnSettings()
        resultDict["update"]["property"] = self.learnProps()
        print(json.dumps(resultDict, indent = 4))
        logger.info("Printed new and different settings, manually add to your config json file if needed")
        return True

    def learnProps(self):
        adb = self.getAdb(self.config.get("common.tools.adb.bin"))
        propsDict = {}
        propsDir = os.path.join(self.tmpDir, "props")
        adb.pull("/data/property", propsDir)
        for f in os.listdir(propsDir):
            if f.startswith("."):
                continue
            fullPath = os.path.join(propsDir, f)
            keys = f.split(".")
            subDict = propsDict
            for i in range(0, len(keys) - 1):
                k = keys[i]
                if k == "persist":
                    continue
                if not k in subDict:
                    subDict[k] = {}
                subDict = subDict[k]


            with open(fullPath, 'r') as fHandle:
                subDict[keys[-1]] = fHandle.read()

        return propsDict



    def learnSettings(self):
        adb = self.getAdb(self.config.get("common.tools.adb.bin"))
        settingsResult = {}
        currSettings = self.config.get("update.settings", {})
        tmpDir = os.path.join(self.tmpDir, "db")
        os.makedirs(tmpDir)
        dbPath = os.path.join(tmpDir, "curr.db")
        dbPathShm = dbPath + "-shm"
        dbPathWal = dbPath + "-wal"

        if not len(currSettings):
            logger.warning("Config does not contain settings data, or overrides settings with no data")

        for identifier, data in currSettings.items():
            path = data["path"]
            settingsResult[identifier] = {
                "path": path
            }

            adb.pull(path, dbPath)
            adb.pull(path + "-shm", dbPathShm)
            adb.pull(path + "-wal", dbPathWal)

            settingsFactory = SettingsDatabaseFactory("/tmp/curr.db")
            tablesKey = "update.settings.%s.data" % (identifier.replace(".", "\\."))
            tablesDict = self.config.get(tablesKey)
            settingsResult[identifier]["data"] = {}
            for table, tableData in tablesDict.items():
                settingsResult[identifier]["data"][table] = {}
                material = settingsFactory.getIterable(table)
                currTableKey = tablesKey + "." + table
                for key, value in material.items():
                    currItemKey = currTableKey + "." + key.replace(".", "\\.")
                    currItemVal = self.config.get(currItemKey, None)

                    if currItemVal is None:
                        settingsResult[identifier]["data"][table][key] = value
                    elif currItemVal != material[key]:
                        settingsResult[identifier]["data"][table][key] = value

        return settingsResult


