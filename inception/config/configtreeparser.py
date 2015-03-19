from .config import Config
import json
import os

class ConfigTreeParser(object):

    KEY_INHERIT = "extends"

    def __init__(self, identifierResolver):
        self.identifierResolver = identifierResolver

    def parseJSON(self, identifier):
        jsonFilePath = self.identifierResolver.resolve(identifier)
        if not jsonFilePath:
            raise ValueError("Couldn't resolve %s" % identifier)
        elif not os.path.exists(jsonFilePath):
            raise ValueError("Invalid config path %s" % jsonFilePath)
        with open(jsonFilePath, "r") as jsonFile:
            jsonData = jsonFile.read()
            parsedJSON = json.loads(jsonData)
            parentIdentifier = parsedJSON[self.__class__.KEY_INHERIT] if self.__class__.KEY_INHERIT in parsedJSON else None
            return Config(identifier,
                          parsedJSON,
                          self.parseJSON(parentIdentifier) if parentIdentifier else None,
                          jsonFilePath
            )