from .config import Config
import json
import os
from inception.constants import InceptionConstants
from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from dulwich import index
import dulwich
import logging
import shutil
from inception.config.sourcesparser import SourcesConfig

logger = logging.getLogger("ConfigTree")

class ConfigTreeParser(object):

    KEY_INHERIT = "__extends__"
    KEY_NOTES    = "__notes__"

    def __init__(self, identifierResolver):
        self.identifierResolver = identifierResolver
        self.notes = []
        self.sourcesConfig = SourcesConfig.parseDefaultSourcesFile()

    def parseJSON(self, identifier):
        self.notes = []
        result = self._parseJSON(identifier, False)

        if len(self.notes):
            print("\n=====================================================")

            while len(self.notes):
                identifier, filePath, noteList = self.notes.pop()
                print("\nNotes from %s: "% (identifier))
                print("======================\n")
                print(filePath)
                print("")
                for noteItem in noteList:
                    print(" - " + noteItem)

                print("\n")

            print("=====================================================\n")



        return result

    def _parseJSON(self, identifier, isFresh = False):
        jsonFilePath = self.identifierResolver.resolve(identifier)
        if not jsonFilePath:
            sources = self.sourcesConfig.getSources(identifier)

            if self.fetchConfig(identifier.replace(".", "_"), sources):
                return self._parseJSON(identifier, True)
            raise ValueError("Couldn't resolve %s" % identifier)
        elif not os.path.exists(jsonFilePath):
            raise ValueError("Invalid config path %s" % jsonFilePath)
        with open(jsonFilePath, "r") as jsonFile:
            jsonData = jsonFile.read()
            parsedJSON = json.loads(jsonData)
            parentIdentifier = parsedJSON[self.__class__.KEY_INHERIT] if self.__class__.KEY_INHERIT in parsedJSON else None
            if isFresh and self.__class__.KEY_NOTES in parsedJSON:
                self.notes.append((identifier, jsonFilePath, parsedJSON[self.__class__.KEY_NOTES]))

            result = Config(identifier,
                          parsedJSON,
                          self._parseJSON(parentIdentifier) if parentIdentifier else None,
                          jsonFilePath
            )

            return result

    def fetchConfig(self, name, lookupRepos):
        dissectedName = name.split("_")
        if len(dissectedName) == 2:
            return self.fetchBase(name, lookupRepos)
        elif len(dissectedName) == 3:
            return self.fetchVariant(name, lookupRepos)
        else:
            raise ValueError("%s is not a valid name" % name)

    def fetchRepo(self, repoName, targetPath, lookupRepos):
        repoPath = repoName + ".git"
        for address in lookupRepos:
            if not address.startswith("https://") and not address.startswith("http://"):
                address = "https://github.com/" + address
            try:
                client = HttpGitClient(address)
                if os.path.exists(targetPath):
                    shutil.rmtree(targetPath)
                os.makedirs(targetPath)
                local = Repo.init(targetPath)
                logger.info("Trying %s/%s" % (address, repoPath))
                remoteRefs = client.fetch(repoPath, local)
                local["HEAD"] = remoteRefs["refs/heads/master"]
                indexFile = local.index_path()
                tree = local["HEAD"].tree
                index.build_index_from_tree(local.path, indexFile, local.object_store, tree)
                logger.info("Fetched %s from %s to %s" % (repoName, address, targetPath))

                if os.path.exists(os.path.join(targetPath, os.path.basename(targetPath) + ".json")):
                    return True
                else:
                    shutil.rmtree(targetPath)
            except dulwich.errors.GitProtocolError:
               continue

        return False

    def fetchVariant(self, variantRepoName, lookupRepos):
        base, variant, target = variantRepoName.split("_")

        repoName = "inception_variant_%s" % variantRepoName
        targetDir = os.path.join(InceptionConstants.VARIANTS_DIR, base, variant, target)

        return self.fetchRepo(repoName, targetDir, lookupRepos)

    def fetchBase(self, baseRepoName, lookupRepo):
        base, target = baseRepoName.split("_")
        repoName = "inception_base_%s" % baseRepoName
        targetDir = os.path.join(InceptionConstants.BASE_DIR, base, target)

        return self.fetchRepo(repoName, targetDir, lookupRepo)


