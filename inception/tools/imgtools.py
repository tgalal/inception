from inception.tools import cmdtools
from inception.generators import BootImgGenerator
from subprocess import CalledProcessError
import os
def unpackimg(unpackerBin, img, out):
    if not os.path.isfile(img):
        raise ValueError("Coudn't find %s to unpack"  % img)
    filename = img.split('/')[-1]
    ramdisk = "%s/%s-ramdisk" % (out, filename)
    kernel = "%s/%s-zImage" % (out, filename)
    dt = "%s/%s-dt" % (out, filename)
    ramdiskDir = os.path.join(out, "ramdisk")
    ramdiskExtracted = ramdiskDir + "/" + filename + "-ramdisk"
    if not os.path.exists(out):
        os.makedirs(out)
    unpackResult = cmdtools.execCmd(unpackerBin, "-i", img, "-o", out, failMessage = "Failed to unpack %s to %s" % (img, out))
    try:
        cmdtools.execCmd("gunzip", ramdisk + ".gz")
    except CalledProcessError as e:
        cmdtools.execCmd("mv", ramdisk + ".gz", ramdisk + ".xz")
        cmdtools.execCmd("unxz", ramdisk + ".xz")

    os.makedirs(ramdiskDir)
    cmdtools.execCmd("mv", ramdisk, ramdiskDir)

    f = open(ramdiskExtracted)
    try:
        cmdtools.execCmd("cpio", "-i", cwd = ramdiskDir, stdin = f)
    finally:
        f.close()
    os.remove(ramdiskExtracted)

    #process unpacker output
    resultList = unpackResult.split('\n')
    bootImgGenerator = BootImgGenerator(None)

    for l in resultList:
        try:
            dissect = l.split(' ')
            key = dissect[0]
            value = " ".join(dissect[1:]) or None
        except ValueError:
            key = l.split(' ')
            value = None

        if key == "BOARD_KERNEL_CMDLINE":
            bootImgGenerator.setKernelCmdLine(value)
        elif key == "BOARD_KERNEL_BASE":
            bootImgGenerator.setBaseAddr("0x" + value)
        elif key == "BOARD_RAMDISK_OFFSET":
            bootImgGenerator.setRamdiskOffset("0x" + value)
        elif key == "BOARD_SECOND_OFFSET":
            bootImgGenerator.setSecondOffset("0x" + value)
        elif key == "BOARD_TAGS_OFFSET":
            bootImgGenerator.setTagsOffset("0x" + value)
        elif key == "BOARD_PAGE_SIZE":
            bootImgGenerator.setPageSize(int(value))
        elif key == "BOARD_SECOND_SIZE":
            bootImgGenerator.setSecondSize(int(value))
        elif key == "BOARD_DT_SIZE":
            bootImgGenerator.setDeviceTreeSize(int(value))

    bootImgGenerator.setKernel(kernel)
    bootImgGenerator.setRamdisk(ramdiskDir)
    bootImgGenerator.setDeviceTree(dt)

    return bootImgGenerator
