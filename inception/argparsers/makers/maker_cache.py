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
        assert make_ext4fsBin, "must set %s to be able to create the cache img" % key
        assert os.path.exists(make_ext4fsBin), \
            "%s does not exist, please update %s to the correct path" % (make_ext4fsBin, key)

        cacheSize = self.config.getMountConfig("cache.size", 33554432)
        assert cacheSize, "__config__.target.mount.cache.size is not set, can't create cache img"
        cacheSparsed= self.getMakeValue("sparsed", False)
        cacheMount = self.config.getMountConfig("cache.mount", "/cache")
        cacheMount = cacheMount[1:] if cacheMount[0] == "/" else cacheMount

        cachePath = os.path.join(workDir, "cache")
        os.mkdir(cachePath)
        gen = CacheImgGenerator(cachePath, make_ext4fsBin)
        gen.setSize(cacheSize)
        gen.setSparsed(cacheSparsed)
        gen.setMountPoint(cacheMount)
        updatePkgPath = os.path.join(outDir, InceptionConstants.OUT_NAME_UPDATE)
        if os.path.exists(updatePkgPath):
            gen.update(updatePkgPath)

        out = os.path.join(outDir, self.getCacheOutName())
        gen.generate(out)
        return out