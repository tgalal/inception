from inception.tools import cmdtools
from inception.common import filetools
from droidtools import unpackbootimg, mkbootimg
import os
import logging
import tempfile
logger = logging.getLogger(__name__)
def unpackimg(img, out, degas = False):
    if not os.path.isfile(img):
        raise ValueError("Coudn't find %s to unpack"  % img)
    filename = img.split('/')[-1]
    ramdisk = "%s/%s-ramdisk" % (out, filename)
    kernel = "%s/%s-zImage" % (out, filename)
    ramdiskDir = os.path.join(out, "ramdisk")
    ramdiskExtracted = ramdiskDir + "/" + filename + "-ramdisk"
    if not os.path.exists(out):
        os.makedirs(out)

    bootImg = unpackbootimg.extract(img, out, mode=unpackbootimg.MODE_DEGAS if degas else unpackbootimg.MODE_STANDARD)
    if bootImg.ramdisk.endswith(".gz"):
         cmdtools.execCmd("gunzip", bootImg.ramdisk)
    else:
        cmdtools.execCmd("unxz", bootImg.ramdisk)

    os.makedirs(ramdiskDir)
    cmdtools.execCmd("mv", ramdisk, ramdiskDir)

    f = open(ramdiskExtracted)
    try:
        cmdtools.execCmd("cpio", "-i", cwd = ramdiskDir, stdin = f)
    finally:
        f.close()
    os.remove(ramdiskExtracted)

    bootImg.kernel = kernel
    bootImg.ramdisk = ramdiskDir

    return bootImg

def packimg(bootImg, out, degas = False):
    ramdisk = bootImg.ramdisk
    with filetools.FileTools.newTmpDir() as tmpWorkDir:
        if os.path.isdir(ramdisk):
            logger.debug("Ramdisk is a dir, generating gzip")

            fileList = tempfile.NamedTemporaryFile()
            fCpio = tempfile.TemporaryFile()
            ramdisk = os.path.join(tmpWorkDir, "ramdisk.cpio.gz")
            fRamdisk = open(ramdisk, "w+b")
            cmdtools.execCmd("find", ".", stdout = fileList, cwd = bootImg.ramdisk)

            fileList.seek(0)
            cmdtools.execCmd("cpio", "-o", "-H", "newc", stdout = fCpio, stdin = fileList, cwd = bootImg.ramdisk)
            fCpio.seek(0)
            cmdtools.execCmd("gzip", stdin = fCpio, stdout = fRamdisk, cwd = bootImg.ramdisk)
            bootImg.ramdisk = ramdisk

            fileList.close()
            fCpio.close()
            fRamdisk.close()

        if degas:
            logger.debug("Packing img in degas mode")

        bootImg.build(out, mode=mkbootimg.MODE_DEGAS if degas else mkbootimg.MODE_STANDARD)
