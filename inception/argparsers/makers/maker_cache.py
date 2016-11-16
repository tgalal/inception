from .maker import Maker
from inception.generators.cacheimg import CacheImgGenerator
import os
from inception.constants import InceptionConstants
import logging
logger = logging.getLogger(__name__)

class CacheMaker(Maker):
    def __init__(self, config):
        super(CacheMaker, self).__init__(config, "cache")

    def make(self, workDir, outDir):

        key, make_ext4fsBin = self.getHostBinary("make_ext4fs")
        updatePkgPath = os.path.join(outDir, InceptionConstants.OUT_NAME_UPDATE)
        assert make_ext4fsBin, "must set %s to be able to create the cache img" % key
        assert os.path.exists(make_ext4fsBin), \
            "%s does not exist, please update %s to the correct path" % (make_ext4fsBin, key)

        cacheSize = self.getMakeValue("size")
        if cacheSize is None: cacheSize = self.config.getMountConfig("cache.size", "auto")

        if type(cacheSize) is not int or cacheSize <= 0:
            cacheSize = os.path.getsize(updatePkgPath) if os.path.exists(updatePkgPath) else 0
            cacheSize = int(cacheSize / (1024 * 1024)) + 10 #safe offset to not fail?
            cacheSize = "%sM" % cacheSize

        cacheSparsed= self.getMakeValue("sparsed", False)
        cacheMount = self.config.getMountConfig("cache.mount", "/cache")
        cacheMount = cacheMount[1:] if cacheMount[0] == "/" else cacheMount

        cachePath = os.path.join(workDir, "cache")
        os.mkdir(cachePath)
        gen = CacheImgGenerator(cachePath, make_ext4fsBin)
        gen.setSize(cacheSize)
        gen.setSparsed(cacheSparsed)
        gen.setMountPoint(cacheMount)
        if os.path.exists(updatePkgPath):
            gen.update(updatePkgPath)

        out = os.path.join(outDir, self.getCacheOutName())
        gen.generate(out)
        return out