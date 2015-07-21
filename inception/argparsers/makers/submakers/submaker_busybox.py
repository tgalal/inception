from .submaker import Submaker
import os
import shutil
class BusyboxSubmaker(Submaker):
    SYMLINKS = [
       "djtimex","arp","ash","awk","base64","basename","bbconfig","blkid","blockdev","brctl","bunzip2","bzcat"
        ,"bzip2","cal","cat","catv","chattr","chgrp","chmod","chown","chroot","clear","cmp","comm","cp","cpio",
       "crond","crontab","cut","date","dc","dd","depmod","devmem","df","diff","dirname","dmesg","dnsd","dos2unix",
       "du","echo","ed","egrep","env","expand","expr","false","fbsplash","fdisk","fgrep","find","flash_lock",
       "flash_unlock","flashcp","flock","fold","free","freeramdisk","fsync","ftpget","ftpput","fuser","getopt",
       "grep","groups","gunzip","gzip","halt","head","hexdump","id","ifconfig","inetd","insmod","install","ionice",
       "iostat","ip","kill","killall","killall5","less","ln","losetup","ls","lsattr","lsmod","lsusb","lzcat","lzma",
       "lzop","lzopcat","man","md5sum","mesg","mkdir","mke2fs","mkfifo","mkfs.ext2","mkfs.vfat","mknod","mkswap",
       "mktemp","modinfo","modprobe","more","mount","mountpoint","mpstat","mv","nanddump","nandwrite","nbd-client",
       "netstat","nice","nohup","nslookup","od","patch","pgrep","pidof","ping","pipe_progress","pkill","pmap",
       "poweroff","printenv","printf","ps","pstree","pwd","pwdx","rdev","readlink","realpath","renice","reset",
       "resize","rev","rm","rmdir","rmmod","route","run-parts","rx","sed","seq","setconsole","setserial","setsid",
       "sh","sha1sum","sha256sum","sha3sum","sha512sum","sleep","sort","split","stat","strings","stty","sum","swapoff",
       "swapon","sync","sysctl","tac","tail","tar","tee","telnet","telnetd","test","tftp","tftpd","time","timeout",
       "top","touch","tr","traceroute","true","ttysize","tune2fs","umount","uname","uncompress","unexpand","uniq",
       "unix2dos","unlzma","unlzop","unxz","unzip","uptime","usleep","uudecode","uuencode","vi","watch","wc","wget",
       "which","whoami","xargs","xz","xzcat","yes","zcat"
    ]

    PATH_SYMLINKS = "/system/xbin"
    def make(self, workDir, updateScriptGenerator = None):
        """
        :param workDir: str
        :param updatescriptgen: UpdateScriptGenerator
        """

        xbinPath = os.path.join(workDir,"system","xbin")
        busyboxTargetPath =  xbinPath + "/busybox"

        key, busyboxBinPath = self.getTargetBinary("busybox")

        assert busyboxBinPath,"Must set %s to busybox path" % key

        self.setValue("update.files.add./system/xbin/busybox", {
            "uid":"0",
            "gid":"2000",
            "mode":"0755",
            "symlinks": [os.path.join(self.__class__.PATH_SYMLINKS, symlink) for symlink in self.__class__.SYMLINKS]
        })

        if not os.path.exists(xbinPath):
            os.makedirs(xbinPath)


        shutil.copy(busyboxBinPath, busyboxTargetPath)
