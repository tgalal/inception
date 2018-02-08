from inception.argparsers.argparser import InceptionArgParser
from inception.argparsers.exceptions import InceptionArgParserException
from inception.constants import InceptionConstants
from inception.config import ConfigTreeParser, DotIdentifierResolver
from inception.common.configsyncer import ConfigSyncer
import sys
import os, shutil, logging, tempfile

logger = logging.getLogger(__name__)

class MakeArgParser(InceptionArgParser):

    def __init__(self, description = "Make mode cmd"):
        super(MakeArgParser, self).__init__(description = description)
        self.makeables = ["package", "boot", "cache", "recovery", "dnx", "update", "installer", "odin", "extras"]

        targetOpts = self.add_mutually_exclusive_group(required = True)
        targetOpts.add_argument('-v', '--variant',action = "store", help="variant config code to use, in the format A.B.C")
        targetOpts.add_argument('-c', '--config', action= 'store', help = "Explicit path to config to use instead of passing variant code, requires --output")

        optionalOpts = self.add_argument_group("Optional opts")
        optionalOpts.add_argument("-o", "--output", action="store", help = "Override default output path")
        optionalOpts.add_argument("-d", "--keep-dirs", action="store_true", help="Keep output hierarchy when default output path is overriden. Default is True, requires -o")
        optionalOpts.add_argument("-w", "--keep-work", action="store_true", help="Don't delete work dir when finished")
        optionalOpts.add_argument("-O", "--keep-output", action="store_true", help="Don't clear output dir before make, will replace files with existing names.")
        optionalOpts.add_argument('--learn-settings', action="store_true",
                                  help= "Learn settings from a connected device, and use in generated update package")


        configQueryOpts = self.add_argument_group("Config query options")
        configQueryOpts.add_argument("--config-list-keys", action="store_true", help="List available signing keys")

        makeOpts = self.add_argument_group("General Make opts")

        for makeable in self.makeables:
            formattedMakeableName = makeable[0].upper() + makeable[1:]
            makeOpts.add_argument("--only-%s" % makeable, action="store_true", help="Make only %s " % formattedMakeableName)

            makeableGp = self.add_argument_group("%s Maker Opts" % formattedMakeableName)
            flagGp = makeableGp.add_mutually_exclusive_group(required = False)
            flagGp.add_argument("--%s" % makeable, dest=makeable, action="store_true", help="Make %s, overrides config" % makeable, default=None)
            flagGp.add_argument("--no-%s" % makeable, dest=makeable, action="store_false", help = "Don't make %s, overrides config " % makeable, default=None)

            if makeable == "recovery":
                makeableGp.add_argument("--recovery-sign", action="store", metavar="keys_name",help="Recovery signing keys name")
                makeableGp.add_argument("--recovery-no-sign", action="store_true")
                makeableGp.add_argument("--recovery-img", action="store")
            elif makeable == "update":
                makeableGp.add_argument("--update-no-reboot", action="store_true", help="Don't reboot after update script executes")
                makeableGp.add_argument("--update-sign", action="store", metavar="keys_name",help="Update signing keys name")

                makeableGp.add_argument("--update-apps", action="store_true", help="Make apps")
                makeableGp.add_argument("--update-no-apps", action="store_true", help="Don't make apps")

                makeableGp.add_argument("--update-settings", action="store_true", help="Make settings")
                makeableGp.add_argument("--update-no-settings", action="store_true", help="Don't make Settings")

                makeableGp.add_argument("--update-network", action="store_true", help="Make network")
                makeableGp.add_argument("--update-no-network", action="store_true", help="Don't make network")

                makeableGp.add_argument("--update-databases", action="store_true", help="Make databases")
                makeableGp.add_argument("--update-no-databases", action="store_true", help="Don't make databases")

                makeableGp.add_argument("--update-adb", action="store_true", help="Make adb")
                makeableGp.add_argument("--update-no-adb", action="store_true", help="Don't make adb")

                makeableGp.add_argument("--update-property", action="store_true", help="Make property")
                makeableGp.add_argument("--update-no-property", action="store_true", help="Don't make property")

                makeableGp.add_argument("--update-busybox", action="store_true", help="Make busybox")
                makeableGp.add_argument("--update-no-busybox", action="store_true", help="Don't make busybox")

                makeableGp.add_argument("--update-restore_stock_recovery", action="store_true", help="Restore stock recovery")
                makeableGp.add_argument("--update-no-restore_stock_recovery", action="store_true", help="Don't restore stock recovery")

                makeableGp.add_argument("--update-root", metavar="method_name", action="store", help="Root the device with the specified root method")
                makeableGp.add_argument("--update-no-root", action="store_true", help="Don't root the device")


                makeableGp.add_argument("--update-no-sign", action="store_true")

        self.deviceDir = InceptionConstants.VARIANTS_DIR
        self.baseDir = InceptionConstants.BASE_DIR
        identifierResolver = DotIdentifierResolver([self.deviceDir, self.baseDir])
        self.configTreeParser = ConfigTreeParser(identifierResolver)

    def process(self):
        super(MakeArgParser, self).process()
        code = self.args["variant"]
        outDir = self.args["output"]
        if code:
            self.config = self.configTreeParser.parseJSON(code)

            try:
                a, b, c= code.split('.')
            except ValueError as e:
                raise InceptionArgParserException(
                    "Code must me in the format vendor.model.variant"
                )

            self.setWorkDir(os.path.join(InceptionConstants.WORK_DIR,
                a,
                b,
                c)
            )
        else:
            configPath = self.args["config"]
            if not outDir:
                print("Must set --output when using --config")
                sys.exit(1)
            self.config = self.configTreeParser.parseJSONFile(configPath)
            self.setWorkDir(tempfile.mkdtemp())

        if self.config.get("__abstract__", False, directOnly=True):
            print("Won't make abstract config %s" % code)
            sys.exit(1)
        if self.config.get("__config__") is None:
            sys.stderr.write("You are using an outdated config tree. Please run 'incept sync -v VARIANT_CODE' or set __config__ (see https://goo.gl/aFWPby)\n")
            sys.exit(1)

        makeOnly = []
        for makeable in self.makeables:
            if self.args["only_%s" % makeable]:
                makeOnly.append(makeable)

        for makeable in self.makeables:
            if len(makeOnly):
                self.config.set("%s.__make__" % makeable, makeable in makeOnly)
            elif self.args[makeable] is not None:
                self.config.set("%s.__make__" % makeable, self.args[makeable])

        if self.args["recovery_no_sign"]:
            self.config.set("recovery.keys", None)
        elif self.args["recovery_sign"] is not None:
            self.config.set("recovery.keys", self.args["recovery_sign"])

        if self.args["recovery_img"]:
            self.config.set("recovery.img", self.args["recovery_img"])

        if self.args["update_no_sign"]:
            self.config.set("update.keys", None)
        elif self.args["update_sign"] is not None:
            self.config.set("update.keys", self.args["update_sign"])

        updateMakeables = ("apps", "settings", "databases", "property", "adb", "network", "busybox", "root", "restore_stock_recovery")

        for updateMakeable in updateMakeables:
            if self.args["update_%s" % updateMakeable]:
                if updateMakeable == "restore_stock_recovery":
                    self.config.set("update.%s" % updateMakeable, True)
                elif updateMakeable == "root":
                    self.config.set("update.root_method", self.args["update_%s" % updateMakeable])
                else:
                    self.config.set("update.%s.__make__" % updateMakeable, True)
            elif self.args["update_no_%s" % updateMakeable]:
                if updateMakeable == "restore_stock_recovery":
                    self.config.set("update.%s" % updateMakeable, False)
                elif updateMakeable == "root":
                    self.config.set("update.%s", None)
                else:
                    self.config.set("update.%s.__make__" % updateMakeable, False)

        if self.args["update_no_reboot"]:
            self.config.set("update.script.wait", 60 * 5)


        if outDir:
            self.config.setOutPath(outDir, self.args["keep_dirs"])
        else:
            outDir = self.config.getOutPath()


        if not self.handleConfigQueryArrgs(self.args, self.config):

            self.workDir = self.getWorkDir()
            self.configDir = os.path.dirname(self.config.getSource())

            logger.info("Cleaning work dir " + self.workDir)
            if os.path.exists(self.workDir):
                shutil.rmtree(self.workDir)
            os.makedirs(self.workDir)

            if self.args["learn_settings"]:
                syncer = ConfigSyncer(self.config)
                syncer.applyDiff(syncer.pullAndDiff())

            self.config.make(self.workDir, not self.args["keep_output"])

            if not self.args["keep_work"]:
                logger.info("Cleaning up work dir")
                shutil.rmtree(self.getWorkDir())

        return True


    def handleConfigQueryArrgs(self, args, config):
        if args["config_list_keys"]:
            keys = config.get("__config__.host.keys", {}).keys()
            for i in range(0, len(keys)):
                print("%s- %s" % (i+1, keys[i]))
            return True

        return False

