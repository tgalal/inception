from .maker import Maker
from inception.constants import InceptionConstants
import os
import tarfile
import hashlib
class OdinMaker(Maker):
    def __init__(self, config):
        super(OdinMaker, self).__init__(config, "odin")
    def make(self, workDir, outDir):

        includes = {
            "CSC": [
                os.path.join(outDir, self.getCacheOutName())
            ],
            "AP": [
                os.path.join(outDir, InceptionConstants.OUT_NAME_RECOVERY)
            ],
            "BL": []
        }

        cscProp = self.getMakeProperty("CSC", [])
        apProp = self.getMakeProperty("AP", [])
        blProp = self.getMakeProperty("BL", [])

        for cscFile in cscProp.value:
            includes["CSC"].append(cscProp.resolveRelativePath(cscFile))

        for apFile in apProp.value:
            includes["AP"].append(apProp.resolveRelativePath(apFile))

        for blFile in blProp.value:
            includes["BL"].append(blProp.resolveRelativePath(blFile))

        resultTars = []

        for key, paths in includes.items():
            if not len(paths):
                continue
            outTarPath = os.path.join(outDir, key + "_" + InceptionConstants.OUT_NAME_ODIN.format(identifier = self.config.getIdentifier().replace(".", "-")))
            checksummedOutTar = outTarPath + ".md5"
            with tarfile.TarFile(outTarPath, "w", format = tarfile.USTAR_FORMAT) as outTarFile:
                for path in paths:
                    if os.path.exists(path):
                        outTarFile.add(path, os.path.basename(path))
                    else:
                        raise ValueError("%s does not exist" % path)

            if self.getMakeValue("checksum", True):
                with open(outTarPath, "rb") as outTarFile:
                    md5sum = hashlib.md5(outTarFile.read()).hexdigest()

                with open(outTarPath, "ab") as outTarFile:
                    outTarFile.write(md5sum + "  " + os.path.basename(outTarPath) + "\n")

                os.rename(outTarPath, checksummedOutTar)

            resultTars.append(checksummedOutTar)


        return resultTars
