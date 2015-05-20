from .maker import Maker
from inception.generators.cacheimg import CacheImgGenerator
import os

class CacheMaker(Maker):
    def __init__(self, config):
        super(CacheMaker, self).__init__(config, "cache")

    def make(self, workDir, outDir):
        make_ext4fsBin = self.getCommonConfigValue("tools.make_ext4fs.bin")
        cacheSize = self.getMakeConfigValue("size")
        cacheSparsed= self.getMakeConfigValue("sparsed", False)
        cacheMount = self.getMakeConfigValue("mount", "cache")
        cacheMount = cacheMount[1:] if cacheMount[0] == "/" else cacheMount

        cachePath = os.path.join(workDir, "cache")
        os.mkdir(cachePath)
        gen = CacheImgGenerator(cachePath, make_ext4fsBin)
        gen.setSize(cacheSize)
        gen.setSparsed(cacheSparsed)
        gen.setMountPoint(cacheMount)
        updatePkgPath = os.path.join(outDir, "update.zip")
        if os.path.exists(updatePkgPath):
            gen.update(updatePkgPath)
        gen.generate(os.path.join(outDir, "cache.img"))
