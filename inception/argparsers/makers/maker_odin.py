from .maker import Maker
from inception.constants import InceptionConstants
import os
import tarfile
import hashlib
class OdinMaker(Maker):
    def __init__(self, config):
        super(OdinMaker, self).__init__(config, "odin")
    def make(self, workDir, outDir):
        allIncludes = [
            self.getCacheOutName(),
            InceptionConstants.OUT_NAME_RECOVERY,
            InceptionConstants.OUT_NAME_BOOT
        ]

        outTarPath = os.path.join(outDir, InceptionConstants.OUT_NAME_ODIN.format(identifier = self.config.getIdentifier().replace(".", "-")))
        checksummedOutTar = outTarPath + ".md5"
        with tarfile.TarFile(outTarPath, "w", format = tarfile.USTAR_FORMAT) as outTarFile:
            for inc in allIncludes:
                incPath = os.path.join(outDir, inc)
                if os.path.exists(incPath):
                    outTarFile.add(incPath, os.path.basename(incPath))

        if self.getMakeValue("checksum", True):
            with open(outTarPath, "rb") as outTarFile:
                md5sum = hashlib.md5(outTarFile.read()).hexdigest()

            with open(outTarPath, "ab") as outTarFile:
                outTarFile.write(md5sum + "  " + os.path.basename(outTarPath) + "\n")

            os.rename(outTarPath, checksummedOutTar)

            return checksummedOutTar

        return outTarPath
