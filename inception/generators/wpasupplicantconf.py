from generator import Generator

class EAPProps(object):
    def __init__(self, eap, identity, ca_cert, client_cert, key_id, engine_id=None):
        self.eap = eap
        self.identity = identity
        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.key_id = key_id
        self.engine_id = engine_id or "keystore"

class WPASupplicantNetwork(object):

    def __init__(self, ssid, security, key = None, priority = 1, eapProps=None):
        self.ssid = ssid
        self.security = security
        self.key = key
        self.hidden = False
        self.priority = priority
        self.eapProps = eapProps

        self.validKeyMgmt = ("WPA-PSK", "WPA-EAP")

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

    TEMPLATE_NETWORK_EAP_TLS = u"""
network={{
    ssid="{ssid}"
    scan_ssid={scan_ssid}
    key_mgmt=WPA-EAP IEEE8021X
    eap=TLS
    identity="{identity}"
    ca_cert="{ca_cert}"
    client_cert="{client_cert}"
    engine_id="{engine_id}"
    key_id="{key_id}"
    engine=1
    proactive_key_caching=1
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

    def add_eap_tls_network(self, ssid, eap, identity, ca_cert, client_cert, key_id, engine_id=None, hidden=False):
        eapProps = EAPProps(eap, identity, ca_cert, client_cert, key_id, engine_id)
        network = WPASupplicantNetwork(ssid, "WPA-EAP", eapProps=eapProps)
        if hidden == True:
            network.setHidden(True)
        self.networks.append(network)

    def generate(self):
        networksStr = ""
        for n in self.networks:
            if n.getKeyMgmt() == "WPA-EAP":
                eapProps = n.eapProps
                assert(eapProps is not None), "EAP props not set"
                assert eapProps.eap == "TLS", "Only TLS is supported at the moment for EAP secured networks"
                nStr = WPASupplicantConfGenerator.TEMPLATE_NETWORK_EAP_TLS.format(
                    ssid=n.getSsid(),
                    scan_ssid=1 if n.isHidden() else 0,
                    identity=eapProps.identity,
                    ca_cert=eapProps.ca_cert,
                    client_cert=eapProps.client_cert,
                    engine_id=eapProps.engine_id,
                    key_id=eapProps.key_id
                )
            else:
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
