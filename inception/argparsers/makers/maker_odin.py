from .maker import Maker
from inception.constants import InceptionConstants
import os
import tarfile
import hashlib
class OdinMaker(Maker):
    def __init__(self, config):
        super(OdinMaker, self).__init__(config, "odin")
    def make(self, workDir, outDir):
        odinOutDir = os.path.join(outDir, self.config.getOdinOutPath())
        if not os.path.exists(odinOutDir):
            os.makedirs(odinOutDir)
        flatten = self.getMakeValue("flatten", False)
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
        tarTmps = []

        for key, paths in includes.items():
            if not len(paths):
                continue

            if flatten:
                outTarPath = os.path.join(odinOutDir, InceptionConstants.OUT_NAME_ODIN.format(identifier = self.config.getIdentifier().replace(".", "-")))
            else:
                outTarPath = os.path.join(odinOutDir, key + "_" + InceptionConstants.OUT_NAME_ODIN.format(identifier = self.config.getIdentifier().replace(".", "-")))

            with tarfile.TarFile(outTarPath, "a", format = tarfile.USTAR_FORMAT) as outTarFile:
                for path in paths:
                    if os.path.exists(path):
                        outTarFile.add(path, os.path.basename(path))
                    else:
                        raise ValueError("%s does not exist" % path)



            tarTmps.append(outTarPath)

        if self.getMakeValue("checksum", True):
            for tarTmp in set(tarTmps):
                checksummedOutTar = tarTmp + ".md5"
                with open(tarTmp, "rb") as outTarFile:
                    md5sum = hashlib.md5(outTarFile.read()).hexdigest()

                with open(tarTmp, "ab") as outTarFile:
                    outTarFile.write(md5sum + "  " + os.path.basename(tarTmp) + "\n")

                os.rename(tarTmp, checksummedOutTar)
                resultTars.append(checksummedOutTar)
        else:
            resultTars.extend(tarTmps)

        return resultTars
