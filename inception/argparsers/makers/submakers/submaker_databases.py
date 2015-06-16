from .submaker import Submaker
import logging
import os
import sqlite3
from inception.common.database import Database
logger = logging.getLogger(__name__)
class DatabasesSubmaker(Submaker):
    def make(self, workDir):
        allSettings = self.getValue(".", {})
        for name, dbData in allSettings.items():
            if name == "__make__":
                continue
            elif "__make__" in dbData and dbData["__make__"] is False:
                continue
            elif "__depend__" in dbData:
                targetDep = self.getMaker().getConfig().get(dbData["__depend__"], None)
                if not targetDep or ("__make__" in targetDep and targetDep["__make__"] == False):
                    continue

            path = workDir + dbData["path"]
            if not "version" in dbData:
               raise ValueError("Must specify db version for %s " % name)
            logger.debug("Making %s" % dbData["path"])


            schemaProp = self.getProperty(name.replace(".", "\.") + ".schema")
            schemaPath = schemaProp.resolveAsRelativePath()
            if schemaPath and os.path.exists(schemaPath):
                with open(schemaPath, "r") as schemaFile:
                    schemaData = schemaFile.read()
            else:
                schemaData = schemaProp.getValue()

            db = Database(schemaData)

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            if os.path.exists(path):
                os.remove(path)

            conn = sqlite3.connect(path)

            for tableName, data in dbData["data"].items():
                table = db.getTable(tableName)
                assert table, "Table %s is not in supplied schema" % tableName
                for row in data:
                    table.createRow(**row)

            conn.executescript("PRAGMA user_version = %s;" % dbData["version"])
            conn.executescript(schemaData)
            queries = db.getQueries()
            for q in queries:
                conn.execute(q)

            conn.commit()
            conn.close()
