from inception.common.filetools import FileTools
from inception.common.database import Database
from inception.common.fstabtools import Fstab
import os
import logging
from inception.common.moduletools import ModuleTools
logger = logging.getLogger(__file__)


def ensureDataMounted(fn):
    def wrapped(self, *args):
        self.adb.shell("mount /data")
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
            dbPathJournal = dbPath + "-journal"

            if not len(currSettings):
                logger.warning("Config does not contain settings data, or overrides settings with no data")


            for identifier, data in currSettings.items():
                if identifier == "__make__":
                    continue
                path = data["path"]

                try:
                    self.adb.pull(path, dbPath)
                    try:
                        self.adb.pull(path + "-shm", dbPathShm)
                    except adb.usb_exceptions.AdbCommandFailureException:
                        pass

                    try:
                        self.adb.pull(path + "-wal", dbPathWal)
                    except (adb.usb_exceptions.AdbCommandFailureException, adb.usb_exceptions.ReadFailedError):
                        pass

                    try:
                        self.adb.pull(path + "-journal", dbPathJournal)
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
                except adb.usb_exceptions.AdbCommandFailureException:
                    logger.warning("Failed to pull " + path)
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
        import adb
        with FileTools.newTmpDir() as tmpDir:

            mountCommandOutFile = os.path.join(tmpDir, "mount_out")
            mountCommandOut = self.adb.shell("mount")
            with open(mountCommandOutFile, "w") as out:
                out.write(mountCommandOut)

            try:
                recoveryFstabPath = os.path.join(tmpDir, "recovery.fstab")
                self.adb.pull("/etc/recovery.fstab", recoveryFstabPath)
                parsedRecoveryFstab = Fstab.parseFstab(recoveryFstabPath)
            except adb.usb_exceptions.AdbCommandFailureException as ex:
                parsedRecoveryFstab = Fstab.parseFstab(mountCommandOutFile)

            try:
                fstabPath = os.path.join(tmpDir, "fstab")
                self.adb.pull("/etc/fstab", fstabPath)
                parsedFstab = Fstab.parseFstab(fstabPath)

                for entry in parsedFstab.getEntries():
                    recovFstabEntry = parsedRecoveryFstab.getByMountPoint(entry.getMountPoint())
                    recovFstabEntry.setDevice(entry.getDevice())
                return parsedRecoveryFstab
            except (adb.usb_exceptions.AdbCommandFailureException, adb.usb_exceptions.ReadFailedError) as ex:
                return parsedRecoveryFstab

    def getSizeFor(self, device, resolveByName = False):
        if resolveByName:
            device = self.getDeviceByName(device)
        result = self.adb.shell("cat /proc/partitions")
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
        result = self.adb.shell("ls -l %s" % name).strip()
        if "->" in result:
            return result.split("->")[1].strip()
        return name

    @staticmethod
    def diffMounts(config, fstab):
        mountNames = ["cache", "recovery", "system", "data", "boot"]
        out = {}
        for mountName in mountNames:
            mountData = fstab.getByMountPoint("/" + mountName)
            if mountData:
                out[mountName] = {}
                if config.getMountConfig("%s.dev" % mountName) != mountData.getDevice():
                    out[mountName]["dev"] = mountData.getDevice()
                fsType = mountData.getType()
                if not fsType:
                    logger.warning("Couldn't find fs type for %s" % mountName)
                elif fsType.lower() != config.getMountConfig("%s.fs" % mountName, "").lower():
                    out[mountName]["fs"] = fsType

                if config.getMountConfig("%s.mount" % mountName) != mountData.getMountPoint():
                    out[mountName]["mount"] = mountData.getMountPoint()
            else:
                logger.warning("No %s partition data" % mountName)

        if len(out):
            out = {
                "__config__": {
                    "target": {
                        "mount": out
                    }
                }
            }

        return out

    def syncPartitions(self, apply = False):
        out = {
        }

        fstab = self.pullFstab()
        if not fstab:
            logger.critical("Could not parse fstab! Skipping partitions..")
            return {}

        mountNames = ["cache", "recovery", "system", "data", "boot"]

        for mountName in mountNames:
            mountData = fstab.getByMountPoint("/" + mountName)

            if mountData:
                out[mountName] = {}
                if self.config.getMountConfig("%s.dev" % mountName) != mountData.getDevice():
                    out[mountName]["dev"] = mountData.getDevice()

                mountSize = self.getSizeFor(mountData.getDevice())

                if mountSize:
                    if self.config.getMountConfig("%s.size" % mountName) != mountSize:
                        out[mountName]["size"] = mountSize
                elif mountName == "cache":
                    logger.warning("Wasn't able to detect %s size" % mountName)

                fsType = mountData.getType()
                if not fsType:
                    logger.warning("Couldn't find fs type for %s" % mountName)
                elif fsType.lower() != self.config.getMountConfig("%s.fs" % mountName, "").lower():
                    out[mountName]["fs"] = fsType


                if self.config.getMountConfig("%s.mount" % mountName) != mountData.getMountPoint():
                    out[mountName]["mount"] = mountData.getMountPoint()

            else:
                logger.warning("No %s partition data" % mountName)

        if len(out):
            out = {
                "__config__": {
                    "target": {
                        "mount": out
                    }
                }
            }

        if apply:
            for k, v in out.items():
                self.config.setRecursive(k, v)
        return out

    @ensureDataMounted
    def syncProps(self, apply = False):
        propsDict = {}
        with FileTools.newTmpDir() as tmpDir:
            propsDir = os.path.join(tmpDir, "props")
            os.makedirs(propsDir)
            self.adb.superPull("/data/property", propsDir, fallback=True)
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
        try:
            cmd = "dd if=%s of=%s" % (device, remotePath)
            logger.info(cmd)
            self.adb.shell(cmd)
            self.adb.pull(remotePath, localPath)
            self.config.set(configKey, os.path.relpath(out + "/" + os.path.basename(localPath), relativeTo))
        except:
            logger.warning("Coudn't pull %s" % device)
