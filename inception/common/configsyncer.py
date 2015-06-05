from inception.tools.adbwrapper import Adb
from inception.common.filetools import FileTools
from inception.common.database import Database
import os
import logging
import adb
import json
logger = logging.getLogger(__file__)
class ConfigSyncer(object):
    def __init__(self, config):
        self.config = config
        self.adb = Adb()

    def pullAndDiff(self):
        fullDiff = {
                "settings": {},
                "databases": {}
        }
        with FileTools.newTmpDir() as tmpDir:
            currSettings = self.config.get("update.settings", {})
            tmpDir = os.path.join(tmpDir, "db")
            os.makedirs(tmpDir)
            dbPath = os.path.join(tmpDir, "curr.db")
            dbPathShm = dbPath + "-shm"
            dbPathWal = dbPath + "-wal"

            if not len(currSettings):
                logger.warning("Config does not contain settings data, or overrides settings with no data")


            for identifier, data in currSettings.items():
                if identifier == "__make__":
                    continue
                path = data["path"]

                self.adb.pull(path, dbPath)
                try:
                    self.adb.pull(path + "-shm", dbPathShm)
                except adb.usb_exceptions.AdbCommandFailureException:
                    pass

                try:
                    self.adb.pull(path + "-wal", dbPathWal)
                except (adb.usb_exceptions.AdbCommandFailureException, adb.usb_exceptions.ReadFailedError):
                    pass

                # databaseConfig = self.config.get("update.databases.%s" % identifier.replace(".", "\."), {"data": {}})
                schemaProperty = self.config.getProperty("update.settings.%s.schema" % identifier.replace(".", "\."))
                data["schema"] = schemaProperty.resolveAsRelativePath()
                diffSettingsConfig, databaseConfig = self.diffSettings(data, dbPath)

                databaseConfig["__depend__"] = "update.settings.%s" % identifier.replace(".", "\.")

                fullDiff["settings"][identifier.replace(".", "\.")] = diffSettingsConfig
                fullDiff["databases"][identifier.replace(".", "\.")] = databaseConfig
        return fullDiff


    def applyDiff(self, diffDict):
        databases = diffDict["databases"]
        settings = diffDict["settings"]

        self.config.setRecursive("update.databases", databases)
        self.config.setRecursive("update.settings", settings)



    def diffSettings(self, settings, refDbPath):
        refDb = Database(refDbPath)
        cuffSchemaFile = open(settings["schema"])
        currDb = Database(cuffSchemaFile.read())
        cuffSchemaFile.close()
        diffSettings = {
            "data": {}
        }
        databaseContent = {
            "data": {}
        }

        if not refDb.isEqualSchema(currDb):
            diffSettings["schema"] = refDb.getSchema()

        if not refDb.getVersion() == currDb.getVersion():
            diffSettings["version"] = refDb.getVersion()

        colKeyName = settings["col_key"] if "col_key" in settings else "name"
        colValueName = settings["col_val"] if "col_val" in settings else "value"

        diffSettings["col_key"] = colKeyName
        diffSettings["col_val"] = colValueName

        refSettingsData = settings["data"]

        for table in refDb.getTables():
            if not table.name in refSettingsData:
                databaseContent["data"][table.name] = []
                rows = table.selectRows()
                for row in rows:
                    databaseContent["data"][table.name].append(row.toDict())
            else:
                refSettingsTable = refSettingsData[table.name]

                diffSettings["data"][table.name] = {}

                for row in table.selectRows():
                    key = row.getValueFor(colKeyName)
                    value = row.getValueFor(colValueName)
                    if not key in refSettingsTable or refSettingsTable[key] != value:
                        diffSettings["data"][table.name][key.replace(".", "\.")] = value


        return (diffSettings, databaseContent)


