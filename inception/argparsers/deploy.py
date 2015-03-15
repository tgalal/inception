from argparser import InceptionArgParser
from exceptions import InceptionArgParserException
from .. import InceptionConstants
from .. import Configurator, ConfigNotFoundException
from .. import InceptionExecCmdFailedException
import os, subprocess, json, shutil

class DeployArgParser(InceptionArgParser):

    def __init__(self):
        super(DeployArgParser, self).__init__(description = "Deploy mode cmd")

        targetOpts = self.add_mutually_exclusive_group()
        targetOpts.add_argument('-a', '--all',  action = "store_true")
        targetOpts.add_argument('-v', '--variant', action = "store")

        requiredOpts = self.add_argument_group("Required args")
        requiredOpts.add_argument('-t', '--to', required = True, action = "store")

    def process(self):
        super(DeployArgParser, self).process()
        # try:
        #     configurator = Configurator(self.args["variant"])
        #     vendor, model, variant = self.args["variant"].split('.')
        # except ConfigNotFoundException, e:
        #     raise InceptionArgParserException(e)
        # except ValueError, e:
        #     raise InceptionArgParserException("Code must me in the format vendor.model.variant")

        if not self.args["all"]:
            return self.deployOne(self.args["variant"], self.args["to"])
        else:
            return self.deployAll(self.args["to"])


    def deployAll(self, to):
        probeDir = InceptionConstants.OUT_DIR
        vendors = os.listdir(probeDir)
        result = {}
        for v in vendors:
            models = os.listdir(os.path.join(probeDir, v))
            for m in models:
                variants = os.listdir(os.path.join(probeDir, v, m))
                for c in variants:
                    variantCode = "%s.%s.%s" % (v,m,c)
                    result[variantCode] = self.deployOne(variantCode, to + "/" + variantCode)

        print "\n=================\n\nResult:\n"
        for k,v in result.items():
            print "%s\t\t%s" % ("OK" if v else "Failed", k)

        return True

    def deployOne(self, variantCode, to):
        try:
            vendor, model, variant = variantCode.split('.')
        except ValueError, e:
            raise InceptionArgParserException("Code must me in the format vendor.model.variant")

        sourceDir = os.path.join(InceptionConstants.OUT_DIR, vendor, model, variant)

        if not os.path.exists(to):
            os.makedirs(to)

        toDeploy = ("recovery.img", "cache.img", "manifest.json")

        #verify all files exsits

        for item in toDeploy:
            path = os.path.join(sourceDir, item)
            if not os.path.exists(path):
                print "Couldn't find %s" % path
                return False

        #copy files
        for item in toDeploy:
            src = os.path.join(sourceDir, item)
            self.d("copying", src, to)
            shutil.copy(src, to)

        return True

