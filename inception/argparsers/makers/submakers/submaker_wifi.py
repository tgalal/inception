from .submaker import Submaker
from inception.generators.wpasupplicantconf import WPASupplicantConfGenerator
import os
class WifiSubmaker(Submaker):
    def make(self, workDir):
        aps = self.getValue("aps", [])


        if not len(aps):
            return

        wpaSupplicantData= {
            "mode": "0660",
            "gid": "1010",
            "uid": "1000"
        }

        self.setValue("update.files.add./data/misc/wifi/wpa_supplicant\.conf", wpaSupplicantData)


        gen = WPASupplicantConfGenerator()
        gen.setWorkDir(workDir)



        for ap in aps:
            ssid = ap["ssid"]
            key = ap["key"] if "key" in ap else None
            security = ap["security"] if "security" in ap else None
            security = "WPA-PSK" if key and not security else security
            hidden = ap["hidden"] if "hidden" in ap else False
            prioriy = ap["priority"] if "priority" in ap else 1
            gen.addNetwork(ssid, security, key, hidden, prioriy)

        generated = gen.generate()

        if not os.path.exists(workDir):
            os.makedirs(workDir)

        wpaSupplicantFilePath = os.path.join(workDir, "wpa_supplicant.conf")
        wpaSupplicantFile = open(wpaSupplicantFilePath, "w")
        wpaSupplicantFile.write(generated)
        wpaSupplicantFile.close()