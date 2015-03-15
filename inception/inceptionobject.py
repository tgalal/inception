import subprocess, os
from constants import InceptionConstants

class InceptionExecCmdFailedException(Exception):
    pass

class NoWorkDirException(Exception):
    pass

class NoOutDirException(Exception):
    pass

class InceptionObject(object):

    ADB_INSTANCE = None

    def __init__(self):
        self.workDir = None
        self.outDir = None
        self.logCmd = []

    def d(self, *messages):
        print("%s:\t%s" % (self.__class__.__name__, "\t".join(messages) ))

    def getAdb(self, adbBin):
        if InceptionObject.ADB_INSTANCE:
            return InceptionObject.ADB_INSTANCE

        from tools import Adb

        InceptionObject.ADB_INSTANCE = Adb(adbBin)
        return InceptionObject.ADB_INSTANCE

    def writeCmdLog(self, out):
        f = open(out, "w")
        f.write("\n".join(self.logCmd))
        f.close()

    def execCmd(self, *cmd, **kwargs):
        #cmd = " ".join(cmd)
        failMessage = None if "failMessage" not in kwargs else kwargs["failMessage"]
        cwd = "." if "cwd" not in kwargs else kwargs["cwd"]
        stdin = None if "stdin" not in kwargs else kwargs["stdin"]
        stdout = None if "stdout" not in kwargs else kwargs["stdout"]
        preview = False if "preview" not in kwargs else kwargs["preview"]

        cmdStr = " ".join(cmd)
        self.d(cmdStr)
        self.logCmd.append(cmdStr)
        if not preview:
            try:
                if stdout is not None:
                    result = subprocess.call(cmd, cwd = cwd, stdin = stdin, stdout = stdout, shell = "|" in cmd)
                else:
                    result = subprocess.check_output(cmd, cwd = cwd, stdin = stdin)
            except OSError, e:
                raise InceptionExecCmdFailedException(e)
            except subprocess.CalledProcessError, e:
                raise InceptionExecCmdFailedException(failMessage or e)

            #if result != 0 and failMessage is not None:
            #    raise InceptionExecCmdFailedException(failMessage)
            self.d(str(result))
            return result
        else:
            return True

    def createDir(self, d):
        if not os.path.exists(d):
            self.d("Creating:", d)
            os.mkdir(d)
        else:
            self.d("Exists:", d)

    def createPathString(self, *args):
        return os.path.join(*args)


    def setWorkDir(self, workDir):
        self.workDir = workDir

    def setOutDir(self, outDir):
        self.outDir = outDir

    def getWorkDir(self, *append):
        if not self.workDir:
            raise NoWorkDirException()
        return os.path.join(self.workDir, *append)

    def getOutDir(self):
        if not self.outDir:
            raise NoOutDirException()
        return self.outDir

