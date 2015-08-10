from inception.tools import cmdtools
from inception.common import filetools
from droidtools import unpackbootimg, mkbootimg, minicpio
import os
import logging
import tempfile
import gzip
import sys
import shutil
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
    os.makedirs(ramdiskDir)
    if bootImg.ramdisk.endswith(".gz"):
        with gzip.open(bootImg.ramdisk, 'rb') as gzFile, open(ramdiskExtracted, 'wb') as gunzipped:
                gunzipped.write(gzFile.read())

        os.remove(bootImg.ramdisk)
    else:
        cmdtools.execCmd("unxz", bootImg.ramdisk)

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
            cmdtools.execCmd("find", ".", stdout = fileList, cwd = bootImg.ramdisk)

            fileList.seek(0)
            cmdtools.execCmd("cpio", "-o", "-H", "newc", stdout = fCpio, stdin = fileList, cwd = bootImg.ramdisk)

            fCpio.seek(0)

            with gzip.open(ramdisk, 'wb') as fgzip:
                fgzip.write(fCpio.read())

            bootImg.ramdisk = ramdisk

            fileList.close()
            fCpio.close()

        if degas:
            logger.debug("Packing img in degas mode")

        bootImg.build(out, mode=mkbootimg.MODE_DEGAS if degas else mkbootimg.MODE_STANDARD)
