import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.aro.endpoint import Endpoint

from emuvim.api.aro.arorm import ARORM

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

    def _create_dcs(self):
        rm1 = ARORM(max_cu=4, max_mu=512)
        rm2 = ARORM(max_cu=6, max_mu=512)

        self.dc1 = self.addDatacenter("dc1")
        for sw in self.dc1.switch:
            self.dc1.assignResourceModeltoSw(rm1, sw.name)
        print(self.dc1._RM_switch)

        self.dc2 = self.addDatacenter("dc2", topo='star', sw_param=3)
        for sw in self.dc2.switch:
            self.dc2.assignResourceModeltoSw(rm2, sw.name)
        print(self.dc2._RM_switch)
        # self.dc3 = self.addDatacenter("dc3", topo='mesh', sw_param=3)
        # self.dc4 = self.addDatacenter("dc4", topo='grid', sw_param=[3,4])
        # self.dc5 = self.addDatacenter("dc5", topo='tree', numswitch=3)

    def _create_switches(self):
        self.sw1 = self.addSwitch("sw1", dpid=hex(self._get_next_dpid())[2:])

    def _create_links(self):
        self.addLink(self.dc1, self.sw1)
        self.addLink(self.dc2, self.sw1)
        # self.addLink(self.dc3, self.sw1)
        # self.addLink(self.dc4, self.sw1)

    def _connect_aro(self):
        self.aro = Endpoint("0.0.0.0", 2284, DCnetwork=self)
        self.aro.connectVIM(self.dc1)
        self.aro.connectVIM(self.dc2)
        # self.aro.connectVIM(self.dc3)
        # self.aro.connectVIM(self.dc4)

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
