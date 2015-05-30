import json
from inception.constants import InceptionConstants
import os
class SourcesConfig(object):

    KEY_SOURCES = "__sources__"
    KEY_OVERRIDE = "__override__"
    KEY_DEFAULTS = "__defaults__"

    DEFAULT_SOURCES = {
        "__sources__": ["inception-android"]
    }

    def __init__(self, sourcesJson):
        self.sourcesJson = sourcesJson

    def dumpOriginal(self):
        print(json.dumps(self.sourcesJson, indent=4))

    @classmethod
    def parseSourcesFile(cls,sourcesFilePath):
        with open(sourcesFilePath, "r") as fp:
            jsonFile = json.load(fp)
            return cls(jsonFile)

    @classmethod
    def parseDefaultSourcesFile(cls):
        if not os.path.exists(InceptionConstants.SOURCES_FILE):
            if not os.path.exists(os.path.dirname(InceptionConstants.SOURCES_FILE)):
                os.makedirs(os.path.dirname(InceptionConstants.SOURCES_FILE))

            with open(InceptionConstants.SOURCES_FILE, "w") as f:
                f.write(json.dumps(cls.DEFAULT_SOURCES, indent=4))

        return cls.parseSourcesFile(InceptionConstants.SOURCES_FILE)

    def getSourcesConfig(self, key):
        pass

    def getSources(self, key):
        dissected = key.split(".")
        currContext = self.sourcesJson
        sources = []

        self.__updateSources(sources, currContext)

        for part in dissected:
            if part not in currContext:
                break
            currContext = currContext[part]
            self.__updateSources(sources, currContext)

        return sources[::-1]

    def __updateSources(self, sourcesList, context):
        if self.__class__.KEY_SOURCES in context:
            contextSources = context[self.__class__.KEY_SOURCES]
            assert type(contextSources) is list, "sources must be a list"
            if self.__class__.KEY_OVERRIDE in contextSources:
                del sourcesList[:]

            sourcesList.extend([src for src in contextSources if not src == self.__class__.KEY_OVERRIDE][::-1])
