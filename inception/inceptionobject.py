import subprocess, os, logging
logger = logging.getLogger(__name__)
class InceptionExecCmdFailedException(Exception):
    pass

class NoWorkDirException(Exception):
    pass

class InceptionObject(object):

    ADB_INSTANCE = None

    def __init__(self):
        self.workDir = None
        self.outDir = None

    def d(self, *messages):
        print("%s:\t%s" % (self.__class__.__name__, "\t".join(messages) ))

    def execCmd(self, *cmd, **kwargs):
        #cmd = " ".join(cmd)
        failMessage = None if "failMessage" not in kwargs else kwargs["failMessage"]
        cwd = "." if "cwd" not in kwargs else kwargs["cwd"]
        stdin = None if "stdin" not in kwargs else kwargs["stdin"]
        stdout = None if "stdout" not in kwargs else kwargs["stdout"]
        preview = False if "preview" not in kwargs else kwargs["preview"]

        cmdStr = " ".join(cmd)
        logger.debug(cmdStr)
        if not preview:
            try:
                if stdout is not None:
                    result = subprocess.call(cmd, cwd = cwd, stdin = stdin, stdout = stdout, shell = "|" in cmd)
                else:
                    result = subprocess.check_output(cmd, cwd = cwd, stdin = stdin)
            except OSError as e:
                raise InceptionExecCmdFailedException(e)
            except subprocess.CalledProcessError as e:
                raise InceptionExecCmdFailedException(failMessage or e)

            #if result != 0 and failMessage is not None:
            #    raise InceptionExecCmdFailedException(failMessage)
            logger.debug(str(result))
            return result
        else:
            return True



    def setWorkDir(self, workDir):
        self.workDir = workDir


    def getWorkDir(self, *append):
        if not self.workDir:
            raise NoWorkDirException()
        return os.path.join(self.workDir, *append)