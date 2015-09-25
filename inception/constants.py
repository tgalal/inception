import os
class InceptionConstants:
    INCEPTION_DIR = os.environ.get("INCEPTION_HOME") or os.path.expanduser("~/.inception")
    SOURCES_FILE = os.path.join(INCEPTION_DIR, "sources.json")
    VARIANTS_DIR = os.path.join(INCEPTION_DIR, "variants")
    BASE_DIR = os.path.join(INCEPTION_DIR, "base")
    WORK_DIR = os.path.join(INCEPTION_DIR, "work")
    OUT_DIR = os.path.join(INCEPTION_DIR, "out")
    OUT_NAME_ODIN = "inception-{identifier}.tar"
    OUT_NAME_PACKAGE = "inception-{identifier}.zip"
    OUT_NAME_UPDATE = "update.zip"
    OUT_NAME_RECOVERY = "recovery.img"
    OUT_NAME_BOOT     = "boot.img"
    OUT_NAME_CACHE    = "cache.img"
    OUT_NAME_CONFIG   = "config.json"
    OUT_NAME_SYSTEM   = "system.img" 
    FS_DIR  = "fs"
    # PATH_RSA_KEY = os.path.join(INCEPTION_DIR, "inception_adbkey")
    PATH_RSA_KEY = os.path.expanduser("~/.android/adbkey")
