from .submaker import Submaker
from inception.common.database import Database
import os
import sys
import logging
logger = logging.getLogger(__name__)

class SettingsSubmaker(Submaker):
    def make(self, workDir):
        allSettings = self.getValue(".")
        for name, dbData in allSettings.items():
            if name == "__make__":
                continue
            elif "__make__" in dbData and dbData["__make__"] is False:
                continue
            if not "version" in dbData:
                raise ValueError("Must specify db version for %s " % name)
            if not "schema" in dbData:
                raise ValueError("Must specify db schema for %s" % name)

            schemaProp = self.getProperty(name.replace(".", "\.") + ".schema")
            schemaPath = schemaProp.resolveAsRelativePath()
            if schemaPath and os.path.exists(schemaPath):
                with open(schemaPath, "r") as schemaFile:
                    schemaData = schemaFile.read()
            else:
                schemaData = schemaProp.getValue()

            if not schemaData:
                print("Error: Schema not not set")
                sys.exit(1)

            targetDatabaseConfigItem = {
                "path": dbData["path"],
                "schema": schemaData,
                "version": dbData["version"],
                "data": {}
            }
            colKey = "name" if "col_key" not in dbData else dbData["col_key"]
            colVal = "value" if "col_val" not in dbData else dbData["col_val"]

            db = Database(schemaData)

            for tableName, data in dbData["data"].items():
                table = db.getTable(tableName)
                if not table:
                    logger.warn("Skipping table %s as it's not in supplied schema" % tableName)
                    continue
                if tableName not in targetDatabaseConfigItem["data"]:
                    targetDatabaseConfigItem["data"][tableName] = []

                for key, val in data.items():
                    if key.startswith("__") and key.endswith("__"):
                        continue
                    targetDatabaseConfigItem["data"][tableName].append({
                        colKey: key,
                        colVal: val
                    })

            self.setValue("update.databases.%s" % name.replace(".", "\."), targetDatabaseConfigItem)



