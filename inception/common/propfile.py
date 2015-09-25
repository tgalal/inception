from inception.config import Config
import os
class PropFile(object):
    def __init__(self, filePath):
        self._config = Config.new(identifier=os.path.basename(filePath), template={})
        self.rawProps = []
        with open(filePath, 'r') as f:
            for l in f.readlines():
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                k,v = l.split('=', 1)
                self._config.set(k, v)
                self.rawProps.append((k, v))

    def get(self, key):
        return self._config.get(key)

    def set(self, key, val):
        self._config.set(key, val)


    def __str__(self):
        return "\n".join([prop[0] + "=" + prop[1] for prop in self.rawProps])

class DefaultPropFile(PropFile):
    def getProductCpuABI(self):
        return self.get("ro.product.cpu.abi")

    def getArch(self):
        arch = self.getProductCpuABI()
        if not arch:
            return None
        if arch.startswith("arm"):
            return "arm"

        return arch

    def getProductManufacturer(self):
        return self.get("ro.product.manufacturer")

    def getProductBrand(self):
        return self.get("ro.product.brand")

    def getProductModel(self):
        return self.get("ro.product.model")

    def getProductBoard(self):
        return self.get("ro.product.board")

    def getProductDevice(self):
        return self.get("ro.product.device")

    def getProductName(self):
        return self.get("ro.product.name")

    def getBoardPlatform(self):
        return self.get("ro.board.platform")

    def getBuildProduct(self):
        return self.get("ro.build.product")

    def getConfigKnox(self):
        return self.get("ro.config.knox")

    def getReleaseVersion(self):
        return self.get("ro.build.version.release")
