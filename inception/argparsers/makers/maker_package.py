from .maker import Maker
from inception.constants import InceptionConstants
import os
import zipfile
from collections import OrderedDict
import json
import hashlib
class PackageMaker(Maker):
    def __init__(self, config):
        super(PackageMaker, self).__init__(config, "package")
    def make(self, workDir, outDir):
        allIncludes = []
        excludes = self.getMakeValue("exclude", [])
        if "cache" not in excludes:
            allIncludes.append(self.getCacheOutName())

        if "update" not in excludes:
            allIncludes.append(InceptionConstants.OUT_NAME_UPDATE)

        if "recovery" not in excludes:
            allIncludes.append(InceptionConstants.OUT_NAME_RECOVERY)

        if "boot" not in excludes:
            allIncludes.append(InceptionConstants.OUT_NAME_BOOT)

        if "config" not in excludes:
            allIncludes.append(InceptionConstants.OUT_NAME_CONFIG)

        if "system" not in excludes:
            allIncludes.append(self.getSystemOutName())

        outZipPath = os.path.join(outDir, InceptionConstants.OUT_NAME_PACKAGE.format(identifier = self.config.getIdentifier().replace(".", "-")))
        m = Manifest(self.config.identifier)
        with zipfile.ZipFile(outZipPath, "w") as outZipFile:
            for inc in allIncludes:
                incPath = os.path.join(outDir, inc)
                if os.path.exists(incPath):
                    m.add(incPath, os.path.dirname(incPath))
                    outZipFile.write(incPath, os.path.basename(incPath))

            outZipFile.writestr("manifest.json", m.toJSON())

        return outZipPath


class Manifest(object):
    MANIFEST_VERSION = 1
    def __init__(self, identifier):
        self.identifier = identifier
        self.files = []

    def add(self, path, relativeTo):
        with open(path, 'rb') as f:
            hsh = hashlib.sha1(f.read()).hexdigest()
            self.files.append((os.path.relpath(path, relativeTo), hsh))

    def toJSON(self):
        data = OrderedDict([
            ("id", self.identifier),
            ("version", Manifest.MANIFEST_VERSION),
            ("files", OrderedDict(self.files))
        ])


        return json.dumps(data, indent=4)
