from .submaker import Submaker
import collections
import os

class PropertySubmaker(Submaker):
    def make(self, workDir):
        props = self.getValue(".", {})
        if "__make__" in props:
            del props["__make__"]

        if "__depend__" in props:
            del props["__depend__"]

        propsFlat = self.flatten(props)
        outDir = os.path.join("data", "property")
        localOutDir = os.path.join(workDir, outDir)
        if len(propsFlat):
            os.makedirs(localOutDir)
            self.setValue("update.files.add.data/property", {
                "destination": "/data/property",
                "uid": "0",
                "gid": "0",
                "mode": "0600",
                "mode_dirs": "0700"
            })

        for fname, val in propsFlat.items():
            if not val:
                continue

            if fname.endswith("__val__"):
                fname = fname.replace(".__val__", "")

            fname = "persist.%s" % fname
            with open(os.path.join(localOutDir, fname), "w") as propFile:
                propFile.write(val)
            #escapedFname = fname.replace(".", "\.")
            #self.setConfigValue("update.files.add.data/property/%s" % escapedFname, self._getPropFileData(fname))

    def _getPropFileData(self, fname):
        return {
            "destination": "/data/property/%s" % fname,
            "uid": "0",
            "gid": "0",
            "mode": "0600"
        }

    def flatten(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


