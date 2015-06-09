from inception.common.filetools import FileTools
from inception.common.database import Database
import os
import logging
from inception.common.moduletools import ModuleTools
logger = logging.getLogger(__file__)
class ConfigSyncer(object):
    def __init__(self, config):
        self.config = config

        ModuleTools.adb(True)
        from inception.tools.adbwrapper import Adb
        self.adb = Adb()

    def pullAndDiff(self):
        import adb

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
                if data["schema"] and not os.path.exists(data["schema"]):
                    data["schema"] = schemaProperty.getValue()
                diffSettingsConfig, databaseConfig = self.diffSettings(data, dbPath)

                databaseConfig["__depend__"] = "update.settings.%s" % identifier.replace(".", "\.")

                fullDiff["settings"][identifier] = diffSettingsConfig
                fullDiff["databases"][identifier] = databaseConfig
        return fullDiff


    def applyDiff(self, diffDict):
        databases = diffDict["databases"]
        settings = diffDict["settings"]

        # self.config.setRecursive("update.databases", databases)

        for key, val in settings.items():
            key = "update.settings." + (key.replace(".", "\."))
            self.config.set(key, {})
            for prop, propVal in val.items():
                if prop == "data":
                    self.config.set(key + ".data", {})
                    for table, tableData in propVal.items():
                        self.config.set(key + ".data." + table, {})
                        for k, v in tableData.items():
                            self.config.set(key + ".data." + table + "." + (k.replace(".", "\.")), v)
                else:
                    self.config.set(key + "." + prop, propVal)

        for key, val in databases.items():
            key = "update.databases." + (key.replace(".", "\."))
            self.config.setRecursive(key, val)

        # self.config.setRecursive("update.settings", settings)


    def diffSettings(self, settings, refDbPath):
        refDb = Database(refDbPath)
        if "schema" in settings and settings["schema"]:
            if os.path.exists(settings["schema"]):
                cuffSchemaFile = open(settings["schema"])
                currDb = Database(cuffSchemaFile.read())
                cuffSchemaFile.close()
            else:
                currDb = Database(settings["schema"])

            if "version" in settings:
                currDb.setVersion(int(settings["version"]))

        else:
            currDb = None
        diffSettings = {
            "data": {}
        }
        databaseContent = {
            "data": {}
        }

        if not currDb or not refDb.isEqualSchema(currDb):
            diffSettings["schema"] = refDb.getSchema()
        if not currDb or not refDb.getVersion() == currDb.getVersion():
            diffSettings["version"] = refDb.getVersion()

        colKeyName = settings["col_key"] if "col_key" in settings else "name"
        colValueName = settings["col_val"] if "col_val" in settings else "value"

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


