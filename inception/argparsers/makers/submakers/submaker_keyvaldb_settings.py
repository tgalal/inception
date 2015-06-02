from .submaker_keyvaldb import KeyValDBSubmaker
import os
import logging
logger = logging.getLogger(__name__)
class SettingsKeyValDBSubmaker(KeyValDBSubmaker):
    def make(self, workDir):
        allSettings = self.getConfigValue(".")
        for name, dbData in allSettings.items():
            if name == "__make__":
                continue
            elif "__make__" in dbData and dbData["__make__"] is False:
                continue
            path = workDir + dbData["path"]

            if not "version" in dbData:
                raise ValueError("Must specify db version for %s " % name)
            logger.debug("Making %s" % dbData["path"])
            schema = None if "schema" not in dbData else dbData["schema"]
            colKey = None if "col_key" not in dbData else dbData["col_key"]
            colVal = None if "col_val" not in dbData else dbData["col_val"]
            os.makedirs(os.path.dirname(path))

            db = dbData["data"]
            self.apply(path, str(dbData["version"]), db, schema = schema, colKey = colKey, colVal = colVal)

            super(SettingsKeyValDBSubmaker, self).make(path)

