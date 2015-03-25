from .submaker_keyvaldb import KeyValDBSubmaker
import os
class SettingsKeyValDBSubmaker(KeyValDBSubmaker):
    def make(self, workDir):
        allSettings = self.getConfigValue(".")
        for name, dbData in allSettings.items():
            path = workDir + dbData["path"]
            os.makedirs(os.path.dirname(path))

            db = dbData["data"]
            for table, data in db.items():
                self.apply(path, table, data)

            super(SettingsKeyValDBSubmaker, self).make(path)

