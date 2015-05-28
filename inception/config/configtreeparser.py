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

logger = logging.getLogger(__file__)

class ConfigTreeParser(object):

    KEY_INHERIT = "__extends__"

    def __init__(self, identifierResolver):
        self.identifierResolver = identifierResolver

    def parseJSON(self, identifier):
        jsonFilePath = self.identifierResolver.resolve(identifier)
        if not jsonFilePath:
            self.fetchBase("inception_base_" + identifier.replace(".", "_"))
            return self.parseJSON(identifier)
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

    def fetchBase(self, baseRepoName):
        _,_, base, variant = baseRepoName.split("_", 3)
        logger.info("Looking for %s" % baseRepoName)
        for address in InceptionConstants.LOOKUP_REPOS:
            try:
                client = HttpGitClient(address)
                targetDir = os.path.join(InceptionConstants.BASE_DIR, base, variant)
                if os.path.exists(targetDir):
                    shutil.rmtree(targetDir)
                os.makedirs(targetDir)
                local = Repo.init(targetDir)
                repoPath = baseRepoName + ".git"
                logger.info("Trying %s/%s " % (address,repoPath))
                remote_refs = client.fetch(repoPath, local)
                local["HEAD"] = remote_refs["refs/heads/master"]
                indexfile = local.index_path()
                tree = local["HEAD"].tree

                index.build_index_from_tree(local.path, indexfile, local.object_store, tree)
                logger.info("Fetched %s from %s to %s" % (baseRepoName, address, targetDir))

            except dulwich.errors.GitProtocolError:
                continue

