from .identifierresolver import IdentifierResolver
import os

class DotIdentifierResolver(IdentifierResolver):
    def __init__(self, lookupPaths = None):
        self.lookupPaths = lookupPaths or []

    def addLookupPath(self, lookupPath):
        self.lookupPaths.append(lookupPath)

    def resolve(self, identifier):
        relativePath = identifier.replace(".", "/")
        jsonConfigPath = os.path.join(relativePath, os.path.basename(relativePath) + ".json")
        for p in self.lookupPaths:
            fullPath = os.path.join(p, jsonConfigPath)
            if os.path.isfile(fullPath):
                return fullPath