from inception.tools import cmdtools
from inception.common import filetools
from droidtools import unpackbootimg, mkbootimg, minicpio
import os
import logging
import gzip
import stat
logger = logging.getLogger(__name__)
def unpackimg(img, out, degas = False):
    if not os.path.isfile(img):
        raise ValueError("Coudn't find %s to unpack"  % img)
    filename = img.split('/')[-1]
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

    fcpio = minicpio.CpioFile()
    fcpio.load_file(ramdiskExtracted)
    for member in fcpio.members:
        path = os.path.join(ramdiskDir, member.name)
        if stat.S_ISDIR(member.mode) and not os.path.exists(path):
            os.makedirs(path)
        else:
            with open(path, 'wb') as outFile:
                outFile.write(member.content)
    os.remove(ramdiskExtracted)

    bootImg.kernel = kernel
    bootImg.ramdisk = ramdiskDir

    return bootImg

def packimg(bootImg, out, degas = False):
    ramdisk = bootImg.ramdisk
    with filetools.FileTools.newTmpDir() as tmpWorkDir:
        if os.path.isdir(ramdisk):
            logger.debug("Ramdisk is a dir, generating gzip")

            ramdisk = os.path.join(tmpWorkDir, "ramdisk.cpio.gz")
            cpioFile = minicpio.CpioFile()

            for root, dirs, files in os.walk(bootImg.ramdisk):
                for file in files:
                    pathAdd =  os.path.join(root, file)
                    cpioFile.add_file(pathAdd, os.path.relpath(pathAdd, bootImg.ramdisk))

            with gzip.open(ramdisk, 'wb') as fgzip:
                fgzip.write(cpioFile.create())

            bootImg.ramdisk = ramdisk

        if degas:
            logger.debug("Packing img in degas mode")

        bootImg.build(out, mode=mkbootimg.MODE_DEGAS if degas else mkbootimg.MODE_STANDARD)
