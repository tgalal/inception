from .submaker import Submaker
import logging
import sys
logger = logging.getLogger(__name__)

class UpdatescriptInitSubmaker(Submaker):
    def make(self, updatePkgDir, updatescriptGen = None):
        updatescriptGen.setVerbose(self.getValue("script.verbose", True))
        mountNames= ["system", "data"]
        dataFormatted = False
        formatData = self.getValue("script.format_data", False)
        formatSupported = self.getTargetConfigValue("bin.update-binary.config.format_supported", False)
        if formatData and formatSupported:
            fsInfo = self.getTargetConfigValue("mount.data", None)
            if fsInfo is not None:
                try:
                    partType = fsInfo["partition_type"] if "partition_type" in fsInfo else None
                    if partType is None:
                        if fsInfo["fs"].lower() in ("ext4", "f2fs"):
                            partType = "EMMC"
                        elif fsInfo["fs"].lower() == "yaffs2":
                            partType = "MTD"
                        else:
                            logger.error(
                                "Could not detect partition type. Please set __config__.target.mount.data.partition_type")
                            sys.exit(1)

                    updatescriptGen.format(fsInfo["fs"], partType, fsInfo["dev"], fsInfo["mount"])
                    dataFormatted = True
                except KeyError as e:
                    logger.error(
                        "data FS info is missing property '%s' required for formatting, doing a normal erase only" %
                        e.args[0])

        for mountName in mountNames:
            updatescriptGen.run("/sbin/mount", "/" + mountName)


        if formatData and not dataFormatted:
            updatescriptGen.rm("/data", recursive=True)


            # dev = self.getMaker().getConfig().getMountConfig(mountName + ".dev")
            # type_ = self.getMaker().getConfig().getMountConfig(mountName + ".type", "EMMC")
            # fs = self.getMaker().getConfig().getMountConfig(mountName + ".fs", "ext4")
            # mountPoint = self.getMaker().getConfig().getMountConfig(mountName + ".mount", "/" + mountName)
            #
            # assert dev, "__config__.target.mount.%s.dev is not set" % mountName
            #
            # updatescriptGen.mount(dev, mountPoint,  fs, type_)
