from inception.argparsers.argparser import InceptionArgParser
from inception.argparsers.exceptions import InceptionArgParserException, MakeUpdatePkgFailedException
from inception.constants import InceptionConstants
from inception.configurator import Configurator, ConfigNotFoundException
from inception.generators import UpdateScriptGenerator
from inception.generators import BootImgGenerator
from inception.generators import WPASupplicantConfGenerator
from inception.generators import CacheImgGenerator
from inception.generators import SettingsGenerator

import sys, os, json, shutil, threading, logging

logger = logging.getLogger(__name__)


class MakeArgParser(InceptionArgParser):
    
    def __init__(self, description = "Make mode cmd"):
        super(MakeArgParser, self).__init__(description = description)

        targetOpts = self.add_mutually_exclusive_group(required = True)
        targetOpts.add_argument('-a', '--all',  action = "store_true")
        targetOpts.add_argument('-v', '--variant',action = "store")

        optionalOpts = self.add_argument_group("Optional opts")
        optionalOpts.add_argument('-x', '--no-cache', 
            required = False, 
            action = "store_true")
        optionalOpts.add_argument('-u', '--no-updatepkg',
            required = False,
            action = "store_true")
        optionalOpts.add_argument("-t", '--threaded', 
            required = False, 
            action = "store_true")

        optionalOpts.add_argument("-m", '--write-manifest',
            required = False,
            action = "store_true")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        self.threads = []



    def process(self):
        super(MakeArgParser, self).process()
        self.threaded = self.args["threaded"]


        # if self.args["threaded"]:
        #     print "Threading not implemented yet"
        #     sys.exit(1)
        if self.args["all"]:
            return self.makeAll()

        return self.make(self.args["variant"],
            writeManifest = self.args["write_manifest"], 
            makeUpdatePkg = not self.args["no_updatepkg"]
            )
        
    
    def makeAll(self):
        result = {}
        probeDir = InceptionConstants.VARIANTS_DIR
        vendors = os.listdir(probeDir)

        def deferredMake(code):
            maker = MakeArgParser()

            try:
                result[code] = maker.make(code, noCache = self.args["no_cache"])
            except:
                result[code] = False

        for v in vendors:
            models = os.listdir(os.path.join(probeDir, v))
            for m in models:
                variants = os.listdir(os.path.join(probeDir, v, m))
                for c in variants:
                    if not os.path.exists(os.path.join(probeDir, v, m, c, c + ".json")):
                        continue
                    variantCode = "%s.%s.%s" % (v,m,c)
                    if self.threaded:
                        thread = threading.Thread(
                            target = lambda: deferredMake(variantCode)
                            )
                        self.threads.append(thread)
                        thread.start()
                    else:
                        self.make(variantCode, noCache = self.args["no_cache"], 
                            writeManifest = self.args["write_manifest"],
                            makeUpdatePkg = not self.args["no_updatepkg"])

        for thread in self.threads:
            thread.join()

        print("\n=================\n\nResult:\n")
        for k,v in result.items():
            print("%s\t\t%s" % ("OK" if v else "Failed", k))


        return True


    def make(self, code, noCache = False, writeManifest = False, makeUpdatePkg = True, newFrontend = True):
        try:
            self.vendor, self.model, self.variant = code.split('.')
        except ValueError as e:
            raise InceptionArgParserException(
                "Code must me in the format vendor.model.variant"
                )

        self.d("MAKING")
        self.d("VENDOR:", self.vendor)
        self.d("MODEL", self.model)
        self.d("VARIANT", self.variant)

        self.setWorkDir(os.path.join(InceptionConstants.WORK_DIR, 
            self.vendor,
            self.model,
            self.variant))
        self.setOutDir(os.path.join(InceptionConstants.OUT_DIR, 
            self.vendor,
            self.model,
            self.variant))
        self.workDir = self.getWorkDir() 
        try:
            self.configurator = Configurator(code)
        except ConfigNotFoundException as e:
            raise InceptionArgParserException(e)
        self.config = self.configurator.getConfig()
        self.configDir = os.path.dirname(self.configurator.getConfigPath())


        self.d("Cleaning work dir " + self.workDir)
        if os.path.exists(self.workDir):
            shutil.rmtree(self.workDir)
        os.makedirs(self.workDir)

        self.d("Cleaning out dir")
        outDir = self.getOutDir() 
        if os.path.exists(outDir):
            shutil.rmtree(outDir)
        os.makedirs(outDir)


        self.buildFS()
        self.applyPatches()
        self.makeSettings()

        updatePkg = self.makeUpdatePkg() if makeUpdatePkg else None
        if not noCache and updatePkg:
            if self.config.get("fstab.cache.size", None) is None:
                logger.warn("fstab.cache.size not set, will not generate cache")
            else:
                self.makeCacheImg(updatePkg)

        imgsConfig = self.config.get("imgs")

        if imgsConfig and "boot" in imgsConfig and imgsConfig["boot"] is not None:
            self.makeBootImg()


        if self.hasRecovery():
            recoveryConfig = self.config.get("config.recovery")
            if "stock_init_bin" in recoveryConfig:
                #cp ramdisk to work
                ramdisk = recoveryConfig["ramdisk"]
                if not os.path.isdir(ramdisk):
                    raise ValueError("Can't yet handle compressed ramdisk in this case")

                modifiedRamdiskPath = os.path.join(self.getWorkDir(), "ramdisk2")

                shutil.copytree(ramdisk, modifiedRamdiskPath, symlinks = True)
                shutil.copy(recoveryConfig["stock_init_bin"], modifiedRamdiskPath)

                if "stock_init_rc_append" in recoveryConfig:
                    origF = open(modifiedRamdiskPath + "/init.rc", "a")
                    appendF = open(recoveryConfig["stock_init_rc_append"], "r")
                    origF.write("\n")
                    origF.write("".join(appendF.readlines()))
                    appendF.close()
                    origF.close()

                gen = self._makeBootImgGenerator("recovery")
                gen.setRamdisk(modifiedRamdiskPath)
                gen.generate(self.getOutDir() + "/recovery.img")
            else:
                self.makeRecoveryImg()

        self.writeUsedConfig()
        self.writeCmdLog(os.path.join(self.getOutDir(), "make.commands.log"))

        if writeManifest:
            self.writeManifest()

        return True

    def resolvePathRelativeToConfig(self, path):
        if path.startswith("/"):
            return path
        return os.path.join(self.configDir, path)

    def hasRecovery(self):
        return self.config.get("config.recovery.ramdisk") is not None

    def writeUsedConfig(self):
        f = open(os.path.join(self.getOutDir(), "config.json"), "w")
        f.write(self.config.toString())
        f.close()

    def makeUpdatePkg(self):
        recoveryConfig = self.config.get("config.recovery")
        writeRecovery = "stock_init_bin" in recoveryConfig
        updatePkgDir = self.createPathString(self.workDir, "update-pkg");
        updateScriptDir = self.createPathString(updatePkgDir, 
            "META-INF/com/google/android")
        self.createDir(updatePkgDir)


        os.makedirs(updateScriptDir)

        self.makeAddDirs(updatePkgDir)
        if len(self.config.get("network.aps", [])):
            self.makeWPASupplicant(updatePkgDir)

        updateScriptPath = self.makeUpdateScript(updateScriptDir, writeRecovery = writeRecovery)
        if updateScriptPath:
            updateBin = self.config.get("config.update-binary.bin")
            shutil.copy(updateBin, updateScriptDir)

            updatePkgPath = self.makeUpdateZip(updatePkgDir)
            shutil.copy(updatePkgPath, os.path.join(self.getOutDir(), "update.zip" ))
            return updatePkgPath
        return False


    def makeUpdateZip(self, src):
        updatePkgZipPath = "../update-unsigned.zip"
        signedUpdatePkgZipPath = "../update.zip"
        self.execCmd("zip", "-q", "-r", "-0", 
            updatePkgZipPath, ".", cwd = src, 
            failMessage="Failed to create Update Package")
        self.d("Created update package")
        self.execCmd("java", 
            "-jar", 
            "/home/tarek/testlab/signapk/SignApk/signapk.jar", 
            "/home/tarek/testlab/signapk/SignApk/testkey.x509.pem",
            "/home/tarek/testlab/signapk/SignApk/testkey.pk8",
            updatePkgZipPath, 
            signedUpdatePkgZipPath,  
            cwd = src, 
            failMessage = "Faield to sign update package")
        #return src + "/../update.zip"
        return os.path.join(src, signedUpdatePkgZipPath)

    def buildFS(self):
        #merge fs folder in all tree
        self.d("Building fs")
        
        fspaths = [self.config.getFSPath()]
        config = self.config
        while not config.isOrphan():
            config = config.getParent()
            fspaths.append(config.getFSPath())

        fspaths.reverse()

        
        for fspath in fspaths:
            if os.path.isdir(fspath):
                self.execCmd("cp", "-r", fspath, self.getWorkDir())        


    def findFile(self, fname, config):
        if fname[0] == "/":
            fname = fname[1:]
        fpath = os.path.join(self.getWorkDir(), InceptionConstants.FS_DIR ,fname)
        if not os.path.exists(fpath):
            raise MakeUpdatePkgFailedException("Couldn't find %s anywhere" % fname)

        return fpath

        # configDirName = os.path.dirname(config.getPath())
        
        # filePath = self.createPathString(configDirName, InceptionConstants.FS_DIR, fname)
        # self.d("Looking for", fname, "as", filePath)

        # if os.path.exists(filePath):
        #     return filePath

        # parentConfig = config.getParent()
        # if parentConfig == None:
        #     raise MakeUpdatePkgFailedException("Couldn't find %s anywhere" % fname)

        #return self.findFile(fname, parentConfig)

    def makeSettings(self):
        settings = self.config.get("settings", {})
        if len(settings):
            for k, v in settings.items():
                if "set" in v:
                    settingsGen = SettingsGenerator(os.path.join(self.getWorkDir(), "fs%s" % v["path"]))
                    settingsGen.generate(v["set"])

        return True

    def makeAddDirs(self, outdir):
        addDirs = self.config.get("fs.add", [])
        for d in addDirs:
            self.d("Looking for", d)
            fpath = self.findFile(d, self.config)
            self.d("Found in", fpath)
            if os.path.isdir(fpath):
                shutil.copytree(fpath, outdir + "/" + d)
            else:
                shutil.copy(fpath, outdir)

    def hasNetworkConfig(self):
        return len(self.config.get("network.aps", [])) > 0

    def makeUpdateScript(self, updateScriptDir, writeRecovery = False):
        u = UpdateScriptGenerator()

        formatData = self.config.get("fstab.data.format", True)

        if writeRecovery:
            u.writeImage("/cache/recovery.img", self.config.get("fstab.recovery.dev"))

        u.mount("/system")
        u.mount("/data")

        for f in self.config.get("fs.rm", []):
            u.rm(f)

        for f in self.config.get("fs.rmdir", []):
            u.rm(f, recursive = True)

        if formatData:
            u.rm("/data", True)

        toAdd = self.config.get("fs.add", [])
        for f in toAdd:
            u.extractDir(f, "/" + f)

        if self.hasNetworkConfig() and not "data" in toAdd:
            u.extractDir("data/misc/wifi", "/data/misc/wifi")

        for path, permissions in self.config.get("files", {}).items():
            if "mode_dirs" in permissions:
                u.setPermissions(path, 
                    permissions["uid"],
                    permissions["gid"],
                    permissions["mode_files"],
                    permissions["mode_dirs"])
            else:
                if not self.hasNetworkConfig() and path == "/data/misc/wifi/wpa_supplicant.conf":
                    continue
                u.setPermissions(path,
                    permissions["uid"],
                    permissions["gid"],
                    permissions["mode"])
        #if not u.isDirty():
        #    return False

        updateScript = u.generate()
        self.d("Writing", updateScriptDir+"/updater-script")
        updateScriptFile = open(updateScriptDir+"/updater-script", "w")
        updateScriptFile.write(updateScript)


        self.d("Checking postinst")
        postinst = self.config.get("config.update-binary.postinst", "")
        if postinst:
            postinstFile = open(postinst)
            updateScriptFile.write("\n" + postinstFile.read())
            postinstFile.close()

        updateScriptFile.close()

        return updateScriptDir+"/updater-script"


    def makeWPASupplicant(self, outdir):
        aps = self.config.get("network.aps", [])

        gen = WPASupplicantConfGenerator()
        gen.setWorkDir(self.getWorkDir())
        gen.setOutDir(self.getOutDir())

        for ap in aps:
            ssid = ap["ssid"]
            security = ap["security"] if "security" in ap else None
            key = ap["key"] if "key" in ap else None
            hidden = ap["hidden"] if "hidden" in ap else False
            prioriy = ap["priority"] if "priority" in ap else 1
            gen.addNetwork(ssid, security, key, hidden, prioriy)

        generated = gen.generate()

        wifiDir = self.createPathString(outdir, "data", "misc", "wifi")
        if not os.path.exists(wifiDir):
            os.makedirs(wifiDir)

        wpaSupplicantFilePath = self.createPathString(wifiDir, "wpa_supplicant.conf")
        wpaSupplicantFile = open(wpaSupplicantFilePath, "w")
        wpaSupplicantFile.write(generated)
        wpaSupplicantFile.close()

        

    def makeCacheImg(self, updatePkgPath = None):
        cacheDir = self.getWorkDir() + "/cache"
        cacheImgoutPath = os.path.join(self.getOutDir(), "cache.img")
        self.createDir(cacheDir)
        ext4fsbin = self.config.get("config.make_ext4fs.bin") or\
            InceptionConstants.PATH_MAKE_EXT4FS_BIN
        gen = CacheImgGenerator(cacheDir, ext4fsbin)
        gen.setWorkDir(self.getWorkDir())
        gen.setOutDir(self.getOutDir())

        for f in self.config.get("fs.cache", []):
            self.d("Adding to cache img: " + self.findFile(f, self.config))
            gen.addFile(self.findFile(f, self.config))


        recoveryConfig = self.config.get("config.recovery")
        if "stock_init_bin" in recoveryConfig:
            self.d("bundling recovery in cache image")
            self.makeRecoveryImg()
            gen.addFile(self.getOutDir() + "/recovery.img")
            os.remove(self.getOutDir() + "/recovery.img")

        cacheConfig = self.config.get("fstab.cache")
        cacheConfigSize = self.config.get("fstab.cache.size")
        if cacheConfigSize is None:
            raise AssertionError("Must set cache size in config")
        gen.setSize(cacheConfig["size"])
        gen.setMountPoint("cache")
        gen.setSparsed("sparsed" not in cacheConfig or cacheConfig["sparsed"]!= False)

        if updatePkgPath:
            gen.update(updatePkgPath)
        gen.generate(cacheImgoutPath, adbBinPath = self.config.get("config.adb.bin"))


    def _makeBootImgGenerator(self, typ):
        bootConfig = self.config.getProperty("config.%s" % typ)
        ramdisk = bootConfig["ramdisk_dir"] if "ramdisk_dir" in bootConfig else None
        if ramdisk is None:
            ramdisk = self.config.getProperty("config.%s.ramdisk" % typ)

        kernel = self.config.getProperty("config.%s.kernel" % typ)

        second = bootConfig["second"] if "second" in bootConfig else None
        cmdline = bootConfig["cmdline"] if "cmdline" in bootConfig else None
        base = bootConfig["base"] if "base" in bootConfig else None
        pagesize = bootConfig["pagesize"] if "pagesize" in bootConfig else None
        ramdisk_offset = bootConfig["ramdisk_offset"] if "ramdisk_offset" in bootConfig\
            else None
        ramdiskaddr = bootConfig["ramdiskaddr"] if "ramdiskaddr" in bootConfig else None
        devicetree = bootConfig["dt"] if "dt" in bootConfig else None
        signature = bootConfig["signature"] if "signature" in bootConfig else None

        gen = BootImgGenerator(self.config.getProperty("config.mkbootimg.bin"))
        gen.setWorkDir(self.getWorkDir())
        gen.setOutDir(self.getOutDir())
        gen.setKernel(kernel)
        gen.setRamdisk(ramdisk)
        gen.setKernelCmdLine(cmdline)
        gen.setSecondBootLoader(second)
        gen.setPageSize(pagesize)
        gen.setBaseAddr(base)
        gen.setRamdiskOffset(ramdisk_offset)
        gen.setDeviceTree(devicetree)
        gen.setSignature(signature)
        gen.setRamdiskAddr(ramdiskaddr)


        return gen
    def makeBootImg(self):
        gen = self._makeBootImgGenerator("boot")
        gen.generate(self.getOutDir() + "/boot.img")

    def makeRecoveryImg(self):
        gen = self._makeBootImgGenerator("recovery")
        gen.generate(self.getOutDir() + "/recovery.img")

    def writeManifest(self):
        manifestData = {
            "title": self.config.get("device.name"),
            "mac_file": self.config.get("device.name"),
            "mac_lower": self.config.get("config.mac.lower", False),
            "detect": self.config.get("device.usb_ids"),
            "cache": {
                "img": "cache.img",
                "partition": self.config.get("fstab.cache.pit_name")
            },
            "boot": {
                "img": "boot.img",
                "partition": self.config.get("fstab.boot.pit_name")
            },
            "recovery": {
                "img": "recovery.img",
                "partition": self.config.get("fstab.recovery.pit_name")
            }
        }

        manifest = open(self.getOutDir() + "/manifest.json", "w")
        manifest.write(json.dumps(manifestData, indent = 4))
        manifest.close()

    def applyPatches(self):
        self.d("Applying patches")
        patchItems = self.config.get("patch", {})
        patchDir = os.path.join(self.getWorkDir(), "patch_work")
        self.createDir(patchDir)
        for target, patches in patchItems.items():
            self.d("Patching", target)
            targetFullPath = self.findFile(target, self.config)
            targetFname, targetExt = os.path.basename(targetFullPath).split('.')
            shutil.copy(targetFullPath, patchDir)
            patchedOutput = patchDir + "/" + "%s.%s_patched" % (targetFname, targetExt)

            if not targetExt == "apk":
                print("Cannot handle non apks at the moment")
                sys.exit(1)

            apktool = self.config.get("config.apktool.bin", None)
            frameworksDir = self.resolvePathRelativeToConfig(self.config.get('config.apktool.frameworks_dir', None))



            java = self.config.get("config.java.bin", None)

            if apktool is None:
                logger.error("config.apktool.bin not set, cannot patch")
                sys.exit(1)

            if frameworksDir is None:
                logger.error("config.apktool.frameworks_dir not set, cannot patch without framework dirs")
                sys.exit(1)

            if java is None:
                logger.error("config.java.bin not set, cannot patch without java bin")
                sys.exit(1)

            cmd = (java,
                "-jar", apktool,
                "decode",
                "--frame-path", frameworksDir,
                "%s.%s" % (targetFname, targetExt))
            logger.warn(cmd)
            self.execCmd(
                *cmd,
                cwd = patchDir)



            for patch in patches:
                path = patch["path"]
                self.d("Applying patch:", os.path.basename(path))
                patchFile = open(path)
                self.execCmd("patch", "-p1", cwd = patchDir + "/" + targetFname, stdin = patchFile)
                patchFile.close()

            self.execCmd(
                java,
                "-jar", apktool,
                "build",
                "-c",
                "--frame-path", frameworksDir,
                "--output", patchedOutput,
                patchDir + "/" + targetFname,
                )

            shutil.copy(patchedOutput, targetFullPath)
