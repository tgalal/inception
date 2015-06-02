import shutil
import tempfile
import os
class FileTools:
    class TmpWorkDir(object):
        def __enter__(self):
            self.__path = tempfile.mkdtemp()
            return self.__path

        def __exit__(self, exc_type, exc_val, exc_tb):
            if os.path.exists(self.__path):
                shutil.rmtree(self.__path)

    @staticmethod
    def newTmpDir():
        return FileTools.TmpWorkDir()