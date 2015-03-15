from argparser import InceptionArgParser
from make import MakeArgParser
from exceptions import InceptionArgParserException
from .. import InceptionConstants
from .. import Configurator, ConfigNotFoundException
from .. import InceptionExecCmdFailedException
#from .. import Adb 
import os, subprocess, json, shutil
from Inception.generators.settings import SettingsDatabaseFactory

class LearnArgParser(InceptionArgParser):

    def __init__(self):
        super(LearnArgParser, self).__init__(description = "Learn mode cmd")

        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-v', '--variant', required = True, action = "store")

    def process(self):
        super(LearnArgParser, self).process()

        try:
            configurator = Configurator(self.args["variant"])
            vendor, model, variant = self.args["variant"].split('.')
        except ConfigNotFoundException, e:
            raise InceptionArgParserException(e)
        #except ValueError, e:
        #    raise InceptionArgParserException("Code must me in the format vendor.model.variant")


        self.config = configurator.getConfig()
        syncFiles = self.config.get("files")
        self.setOutDir(os.path.join(InceptionConstants.OUT_DIR, vendor, model, variant))

        deviceFSDir = os.path.join(os.path.dirname(self.config.getPath()), InceptionConstants.FS_DIR)

        adb = self.getAdb(self.config.get("config.adb.bin"))
        devices = adb.devices()
        deviceMode = devices.itervalues().next()

        for p, conf in syncFiles.items():
            if "sync" in conf and conf["sync"] == False:
                continue
            else:
                #construct directory
                outputDir = os.path.join(deviceFSDir, os.path.dirname(p)[1:], os.path.basename(p))
                adb.pull(
                    p,
                    outputDir,
                    requireSu = self.config.get("config.adb.require-su", False) and deviceMode == "device"
                )

        #settings diff
        settingsResult = {}
        for identifier, data in self.config.get("settings", {}).items():
            settingsResult[identifier] = {
                "path": data["path"]
            }
            path = data["path"]
            settingsFactory = SettingsDatabaseFactory(deviceFSDir + path)

            if "set" in data and type(data["set"]) is dict:
                settingsResult[identifier]["set"] = {} 
                for table, content in data["set"].items():
                    settingsResult[identifier]["set"][table] = {}
                    material = settingsFactory.getIterable(table)
                    
                    for key, value in material.items():#content.items():
                        if key not in data["set"][table]:
                            settingsResult[identifier]["set"][table][key] = value
                        elif data["set"][table][key] != material[key]:
                            settingsResult[identifier]["set"][table][key] = value

        print json.dumps(settingsResult, indent = 4)
        self.d("Printed new and different settings, manually add to your config json file if needed")


        return True

