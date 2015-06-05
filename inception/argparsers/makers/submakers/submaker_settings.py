from .submaker import Submaker
from inception.common.database import Database

class SettingsSubmaker(Submaker):
    def make(self, workDir):
        allSettings = self.getConfigValue(".")
        for name, dbData in allSettings.items():
            if name == "__make__":
                continue
            elif "__make__" in dbData and dbData["__make__"] is False:
                continue
            if not "version" in dbData:
                raise ValueError("Must specify db version for %s " % name)
            if not "schema" in dbData:
                raise ValueError("Must specify db schema for %s" % name)

            schemaPath = self.getConfigProperty(name.replace(".", "\.") + ".schema").resolveAsRelativePath()

            targetDatabaseConfigItem = {
                "path": dbData["path"],
                "schema": schemaPath,
                "version": dbData["version"],
                "data": {}
            }
            colKey = "name" if "col_key" not in dbData else dbData["col_key"]
            colVal = "value" if "col_val" not in dbData else dbData["col_val"]

            with open(schemaPath, "r") as schemaFile:
                db = Database(schemaFile.read())

                for tableName, data in dbData["data"].items():
                    table = db.getTable(tableName)
                    assert table, "Table %s is not in supplied schema" % tableName
                    if tableName not in targetDatabaseConfigItem["data"]:
                        targetDatabaseConfigItem["data"][tableName] = []

                    for key, val in data.items():
                        if key.startswith("__") and key.endswith("__"):
                            continue
                        targetDatabaseConfigItem["data"][tableName].append({
                            colKey: key,
                            colVal: val
                        })

                self.setConfigValue("update.databases.%s" % name.replace(".", "\."), targetDatabaseConfigItem)



