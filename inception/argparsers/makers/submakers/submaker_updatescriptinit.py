from .submaker import Submaker
class UpdatescriptInitSubmaker(Submaker):
    def make(self, updatePkgDir, updatescriptGen = None):
        updatescriptGen.setVerbose(self.getValue("script.verbose", True))
        mountNames= ["system", "data"]

        for mountName in mountNames:
            updatescriptGen.run("/sbin/mount", "/" + mountName)


            # dev = self.getMaker().getConfig().getMountConfig(mountName + ".dev")
            # type_ = self.getMaker().getConfig().getMountConfig(mountName + ".type", "EMMC")
            # fs = self.getMaker().getConfig().getMountConfig(mountName + ".fs", "ext4")
            # mountPoint = self.getMaker().getConfig().getMountConfig(mountName + ".mount", "/" + mountName)
            #
            # assert dev, "__config__.target.mount.%s.dev is not set" % mountName
            #
            # updatescriptGen.mount(dev, mountPoint,  fs, type_)
