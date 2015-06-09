from inception.common.filetools import FileTools
from inception.common.database import Database
from inception.common.fstabtools import Fstab
import os
import logging
from inception.common.moduletools import ModuleTools
logger = logging.getLogger(__file__)


def ensureDataMounted(fn):
    def wrapped(self, *args):
        self.adb.cmd("mount", "/data")
        return fn(self, *args)

    return wrapped

class ConfigSyncer(object):
    def __init__(self, config):
        self.config = config

        ModuleTools.adb(True)
        from inception.tools.adbwrapper import Adb
        self.adb = Adb()

    @ensureDataMounted
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
                        diffSettings["data"][table.name][key] = value


        return (diffSettings, databaseContent)

    def pullFstab(self):
        with FileTools.newTmpDir() as tmpDir:
            recoveryFstabPath = os.path.join(tmpDir, "recovery.fstab")
            self.adb.pull("/etc/recovery.fstab", recoveryFstabPath)
            parsedRecoveryFstab = Fstab.parseFstab(recoveryFstabPath)

            fstabPath = os.path.join(tmpDir, "fstab")
            self.adb.pull("/etc/fstab", fstabPath)
            parsedFstab = Fstab.parseFstab(fstabPath)

            for entry in parsedFstab.getEntries():
                recovFstabEntry = parsedRecoveryFstab.getByMountPoint(entry.getMountPoint())
                recovFstabEntry.setDevice(entry.getDevice())


            return parsedRecoveryFstab

    def getSizeFor(self, device, resolveByName = False):
        if resolveByName:
            device = self.getDeviceByName(device)
        result = self.adb.cmd("cat", "/proc/partitions")
        grep = device.split("/")[-1]
        for l in result.split("\n"):
            l = l.strip()
            if not l:
                continue
            l = " ".join(l.split()).split(" ")
            if l[3] == grep:
                return int(l[2]) * 1024

        if not resolveByName:
            return self.getSizeFor(device, True)
        return None

    def getDeviceByName(self, name):
        result = self.adb.cmd("ls", "-l", name).strip()
        if "->" in result:
            return result.split("->")[1].strip()
        return name

    def syncPartitions(self, apply = False):
        out = {

        }
        fstab = self.pullFstab()
        if not fstab:
            logger.critical("Could not parse fstab! Skipping partitions..")
            return {}

        cacheData = fstab.getByMountPoint("/cache")
        if cacheData:
            if self.config.get("cache.dev") != cacheData.getDevice():
                out["cache"] = { "dev": cacheData.getDevice() }

            cacheSize = self.getSizeFor(cacheData.getDevice())
            if cacheSize:
                if self.config.get("cache.size") != cacheSize:
                    out["cache"]["size"] = cacheSize
            else:
                logger.warning("Wasn't able to detect Cache size")
        else:
            logger.warning("No cache partition data")

        recoveryData = fstab.getByMountPoint("/recovery")
        if recoveryData:
            if self.config.get("recovery.dev") != recoveryData.getDevice():
                out["recovery"] = { "dev": recoveryData.getDevice() }
        else:
            logger.warning("No recovery partition data")

        bootData = fstab.getByMountPoint("/boot")
        if bootData:
            if self.config.get("boot.dev") != bootData.getDevice():
                out["boot"] = { "dev": bootData.getDevice() }
        else:
            logger.warning("No boot partition data")


        if apply:
            for k, v in out.items():
                self.config.setRecursive(k, v)
        return out

    @ensureDataMounted
    def syncProps(self, apply = False):
        propsDict = {}
        with FileTools.newTmpDir() as tmpDir:
            propsDir = os.path.join(tmpDir, "props")
            self.adb.pull("/data/property", propsDir)
            for f in os.listdir(propsDir):
                if f.startswith("."):
                    continue
                fullPath = os.path.join(propsDir, f)
                with open(fullPath, 'r') as fHandle:
                    currFileVal = fHandle.read()
                    keys = f.split(".")
                    if keys[0] == "persist":
                        keys = keys[1:]

                    if currFileVal == self.config.get("update.property." + (".".join(keys)), None):
                        continue

                    subDict = propsDict
                    for i in range(0, len(keys) - 1):
                        k = keys[i]
                        if not k in subDict:
                            subDict[k] = {}

                        if type(subDict[k]) is not dict:
                            subDict[k] = {"__val__": subDict[k]}
                        subDict = subDict[k]


                    subDict[keys[-1]] = currFileVal

        if apply:
            self.config.setRecursive("update.property", propsDict)

        return propsDict

    def syncImg(self, configKey, device, out, relativeTo):
        remotePath = "/sdcard/synced_%s" % configKey
        localPath =  os.path.join(relativeTo, out, os.path.basename(remotePath))
        self.adb.cmd("dd if=%s of=%s" % (device, remotePath))
        self.adb.pull(remotePath, localPath)
        self.config.set(configKey, os.path.relpath(out + "/" + os.path.basename(localPath), relativeTo))
