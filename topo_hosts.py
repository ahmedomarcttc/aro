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
        self._create_vnfhosts()
        self._connect_aro()

    def _create_dcs(self):
        rm1 = ARORM(max_cu=10, max_mu=1024)
        rm2 = ARORM(max_cu=10, max_mu=1024)

        self.dc1 = self.addDatacenter("dc1")
        for sw in self.dc1.switch:
            self.dc1.assignResourceModeltoSw(rm1, sw.name)
        print(self.dc1._RM_switch)

        self.dc2 = self.addDatacenter("dc2", topo='star', sw_param=3)
        for sw in self.dc2.switch:
            self.dc2.assignResourceModeltoSw(rm2, sw.name)
        print(self.dc2._RM_switch)

    def _create_switches(self):
        self.sw1 = self.addSwitch("sw1", dpid=hex(self._get_next_dpid())[2:])

    def _create_links(self):
        self.addLink(self.dc1, self.sw1)
        self.addLink(self.dc2, self.sw1)

    def _create_vnfhosts(self):
        self.vnf1 = self.dc1.startCompute(
            'vnf1',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.1/24'}],
            flavor_name = 'medium'
            )

        self.vnf2 = self.dc2.startCompute(
            'vnf2',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.2/24'}],
            flavor_name = 'large'
            )

    def _connect_aro(self):
        self.aro = Endpoint("0.0.0.0", 2284, DCnetwork=self)
        self.aro.connectVIM(self.dc1)
        self.aro.connectVIM(self.dc2)

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
