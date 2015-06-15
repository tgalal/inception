import logging
import subprocess
logger = logging.getLogger(__name__)
def execCmd(*cmd, **kwargs):
    cwd = "." if "cwd" not in kwargs else kwargs["cwd"]
    stdin = None if "stdin" not in kwargs else kwargs["stdin"]
    stdout = None if "stdout" not in kwargs else kwargs["stdout"]
    preview = False if "preview" not in kwargs else kwargs["preview"]

    cmdStr = " ".join(cmd)
    logger.debug(cmdStr)
    if not preview:
        if stdout is not None:
            result = subprocess.call(cmd, cwd = cwd, stdin = stdin, stdout = stdout, shell = "|" in cmd)
        else:
            result = subprocess.check_output(cmd, cwd = cwd, stdin = stdin)
        logger.debug(str(result))
        return result
    else:
        return True