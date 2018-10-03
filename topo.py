import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.aro.endpoint import Endpoint

logging.basicConfig(level=logging.INFO)
setLogLevel('info')

EXTSWDPID_BASE = 100

class Topology(DCNetwork):

    def __init__(self):
        super(Topology, self).__init__(
            monitor=False,
            enable_learning=True
        )

    def _get_next_dpid(self):
        global EXTSWDPID_BASE
        EXTSWDPID_BASE += 1
        return EXTSWDPID_BASE

    def setup_topo(self):
        self._create_dcs()
        self._create_switches()
        self._create_links()
        self._connect_aro()
        self._create_hostvnf()

    def _create_dcs(self):
        self.dc1 = self.addDatacenter("dc1")
        self.dc2 = self.addDatacenter("dc2", topo='star', numswitch=3)
        self.dc3 = self.addDatacenter("dc3", topo='mesh', numswitch=3)

    def _create_switches(self):
        self.sw1 = self.addSwitch("sw1", dpid=hex(self._get_next_dpid())[2:])

    def _create_links(self):
        self.addLink(self.dc1, self.sw1)
        self.addLink(self.dc2, self.sw1)
        self.addLink(self.dc3, self.sw1)

    def _create_hostvnf(self):
        self.vnf1 = self.dc1.startCompute("vnf1", network=[{'id': 'intf1', 'ip': '10.0.10.1/24'}])
        self.vnf2 = self.dc2.startCompute("vnf2", network=[{'id': 'intf2', 'ip': '10.0.10.2/24'}])
        self.vnf3 = self.dc3.startCompute("vnf3", network=[{'id': 'intf3', 'ip': '10.0.10.3/24'}])

    def _connect_aro(self):
        self.aro = Endpoint("0.0.0.0", 2284)
        self.aro.connectWIM(self)
        self.aro.connectVIM(self.dc1)
        self.aro.connectVIM(self.dc2)
        self.aro.connectVIM(self.dc3)

    def start_topo(self):
        self.start()
        self.aro.start()

    def stop_topo(self):
        self.aro.stop()
        self.stop()

def main():
    t = Topology()
    t.setup_topo()
    t.start_topo()
    t.CLI()
    t.stop_topo()

if __name__ == '__main__':
    main()
