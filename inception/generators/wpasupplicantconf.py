from generator import Generator

class WPASupplicantNetwork(object):

    def __init__(self, ssid, security, key = None, priority = 1):
        self.ssid = ssid
        self.security = security
        self.key = key
        self.hidden = False
        self.priority = priority

        self.validKeyMgmt = ("WPA-PSK", None)

        if security not in self.validKeyMgmt:
            raise ValueError("Invalid security key mgmt:%s " % security)

    def setHidden(self, hidden):
        self.hidden = True if hidden else False

    def isHidden(self):
        return self.hidden

    def getSsid(self):
        return self.ssid

    def getSecurity(self):
        return self.security

    def getKey(self):
        return self.key

    def getKeyMgmt(self):
        if self.security is None:
            return "NONE"
        return self.security


class WPASupplicantConfGenerator(Generator):
    TEMPLATE_NETWORK = u"""
network={{
    ssid="{ssid}"
    key_mgmt={key_mgmt}
    priority={priority}
    scan_ssid={scan_ssid}
"""
    TEMPLATE_CONFIG = u"""
update_config=1
ctrl_interface={interface}
eapol_version=1
ap_scan=1
fast_reauth=1

{networks}
"""

    def __init__(self, interface = "wlan0"):
        super(WPASupplicantConfGenerator, self).__init__()
        self.networks = []
        self.interface = interface

    def addNetwork(self, ssid, security, key = None, hidden = False, priority = 1):
        network = WPASupplicantNetwork(ssid, security, key, priority)
        if hidden == True:
            network.setHidden(True)
        self.networks.append(network)

    def generate(self):
        networksStr = ""
        for n in self.networks:
            nStr = WPASupplicantConfGenerator.TEMPLATE_NETWORK.format(
                ssid = n.getSsid(),
                key_mgmt = n.getKeyMgmt(),
                scan_ssid = 1 if n.isHidden() else 0,
                priority = n.priority
                )

            if n.getKeyMgmt() and n.getKey():
                nStr += "    psk=\"%s\"\n" % n.getKey()

            nStr += "}"

            networksStr += nStr

        return WPASupplicantConfGenerator.TEMPLATE_CONFIG.format(
            interface = self.interface,
            networks = networksStr)
