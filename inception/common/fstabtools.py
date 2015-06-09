class _FstabEntry(object):
    def __init__(self, dev, mount, type_):
        self.dev = dev
        self.mount = mount
        self.type = type_
        self.mode = "rw"

    def getDevice(self):
        return self.dev

    def getMountPoint(self):
        return self.mount

    def setDevice(self, device):
        self.dev = device

    def getType(self):
        return self.type

    def getOptions(self):
        return self.mode

    def __str__(self):
        return "%s %s %s" % (self.getDevice(), self.getMountPoint(), self.getType())

class Fstab(object):
    def __init__(self, source):
        self.source = source
        self.entries = []
        self.valid = True

    @staticmethod
    def parseFstab(path):
        tab = _FstabV2(path)
        if not tab.isValid():
            tab = _FstabV1(path)
            if not len(tab.getEntries()):
                raise ValueError("Coudn't parse fstab")

        return tab

    def isValid(self):
        return self.valid

    def getEntries(self):
        return self.entries

    def addEntry(self, device, mountPoint, type_):
        self.entries.append(_FstabEntry(device, mountPoint, type_))

    def getByMountPoint(self, mountPoint):
        for entry in self.getEntries():
            if entry.getMountPoint() == mountPoint:
                return entry

    def __str__(self):
        return  "\n".join(
            [part.__str__() for part in self.getEntries()]
        )

class _FstabV2(Fstab):
    def __init__(self, source):
        super(_FstabV2, self).__init__(source)
        with open(source, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                if line.startswith("/dev"):
                    self.valid = False
                    break
                dissectedLine = " ".join(line.split()).split(" ")
                if not len(dissectedLine) >= 3:
                    continue
                self.addEntry(dissectedLine[2], dissectedLine[0], dissectedLine[1])

class _FstabV1(Fstab):
    def __init__(self, source):
        super(_FstabV1, self).__init__(source)
        with open(source, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue

                dissectedLine = " ".join(line.split()).split(" ")
                if not len(dissectedLine) >  3:
                    continue
                self.addEntry(dissectedLine[0], dissectedLine[1], dissectedLine[2])
