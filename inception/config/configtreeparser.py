from .config import Config
from .configv2 import ConfigV2
import json
import os
from inception.constants import InceptionConstants
from dulwich.repo import Repo
from dulwich.client import HttpGitClient
from dulwich import index
from dulwich.client import get_transport_and_path
import dulwich
import logging
import shutil
import sys
import urllib2
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
        result = self._parseCode(identifier, False)

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

    def _parseCode(self, identifier, isFresh = False):
        jsonFilePath = self.identifierResolver.resolve(identifier)
        if not jsonFilePath:
            sources = self.sourcesConfig.getSources(identifier)

            if self.fetchConfig(identifier.replace(".", "_"), sources):
                return self._parseCode(identifier, True)
            raise ValueError("Couldn't resolve %s" % identifier)

        return self._parseJSONFile(jsonFilePath, code = identifier, isFresh = isFresh)



    def parseJSONFile(self, jsonFilePath, code = None):
        return self._parseJSONFile(jsonFilePath, code = code)

    def _parseJSONFile(self, jsonFilePath, isFresh = False, code = "inception.current.out"):
        if not os.path.exists(jsonFilePath):
            raise ValueError("Invalid config path %s" % jsonFilePath)

        with open(jsonFilePath, "r") as jsonFile:
            jsonData = jsonFile.read()
            parsedJSON = json.loads(jsonData)
            parentIdentifier = parsedJSON[self.__class__.KEY_INHERIT] if self.__class__.KEY_INHERIT in parsedJSON else None
            if isFresh and self.__class__.KEY_NOTES in parsedJSON:
                self.notes.append((code, jsonFilePath, parsedJSON[self.__class__.KEY_NOTES]))

            result = ConfigV2(code,
                          parsedJSON,
                          self._parseCode(parentIdentifier) if parentIdentifier else None,
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
            # if address.startswith("git+ssh://"):
            #     address = address.replace("git+ssh://", "ssh://")
            if not address.startswith("https://") and not address.startswith("http://") and not address.startswith("git+ssh://"):
                address = "https://github.com/" + address + "/" + repoPath
            else:
                address += "/" + repoPath

            if self.syncRepo(targetPath, address):
                return True

        return False

    def syncRepo(self, targetPath, repoUrl = None):
        assert os.path.exists(targetPath) or repoUrl, "Either repo should exist or supply remote origin"


        if os.path.exists(targetPath):
            try:
                localRepo = Repo(targetPath)
                config = localRepo.get_config()
                try:
                    remoteUrl = config.get(("remote", "origin"), "url")
                except KeyError:
                    remoteUrl = None

                if not remoteUrl:
                    raise ValueError("Repo \"%s\" not configured or has no remote url" % targetPath)

                if repoUrl and repoUrl != remoteUrl:
                    print("Error: Supplied remote URL does not match remote url in repo config!")
                    sys.exit(1)

            except dulwich.errors.NotGitRepository:
                print("Error: %s will be overwritten, delete or move it." % targetPath)
                sys.exit(1)
        else:
            remoteUrl = repoUrl
            os.makedirs(targetPath)
            localRepo = Repo.init(targetPath)

        remoteUrl = str(remoteUrl)

        logger.info("Syncing %s to %s" % (remoteUrl, targetPath))

        client, hostPath = get_transport_and_path(remoteUrl)
        try:
            remoteRefs = client.fetch(hostPath, localRepo)
            logger.info("Synced %s to %s" % (remoteUrl, targetPath))
            localRepo["HEAD"] = remoteRefs["HEAD"]
            localRepo.reset_index()

            config = localRepo.get_config()
            config.set(("remote", "origin"), "url", remoteUrl)
            config.write_to_path()

        except (dulwich.errors.NotGitRepository,dulwich.errors.GitProtocolError):
            shutil.rmtree(targetPath)
            logger.error("GitProtocolError", exc_info=1)
            return False
        except KeyError:
            # Handle wild KeyError appearing.
            # in an ugly way for now
            shutil.rmtree(targetPath)
            return self.syncRepo(targetPath, remoteUrl)
        except Exception as e:
            logger.error("Error syncing repo", exc_info =1)
            return False

        return True



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


