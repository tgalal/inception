import sys
class ModuleTools:
    @staticmethod
    def adb(panic = False):
        try:
            import adb
            return True
        except ImportError:
            if panic:
                print("Error: adb python module is required but not installed. Install via 'pip install adb'")
                sys.exit(1)
            return False