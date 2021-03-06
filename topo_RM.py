import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.aro.endpoint import Endpoint

from emuvim.dcemulator.resourcemodel.upb.simple import UpbSimpleCloudDcRM
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
        rm0 = UpbSimpleCloudDcRM(max_cu=100, max_mu=2048)
        rm1 = ARORM(max_cu=4, max_mu=512)
        rm2 = ARORM(max_cu=6, max_mu=512)

        self.dc1 = self.addDatacenter("dc1")
        self.dc1.assignResourceModel(rm0)

        self.dc2 = self.addDatacenter("dc2", topo='star', sw_param=3)
        self.dc2.assignResourceModel(rm0)

    def _create_switches(self):
        self.sw1 = self.addSwitch("sw1", dpid=hex(self._get_next_dpid())[2:])

    def _create_links(self):
        self.addLink(self.dc1, self.sw1)
        self.addLink(self.dc2, self.sw1)

    def _create_vnfhosts(self):
        self.vnf1 = self.dc1.startCompute(
            'vnf1',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.1/24'}]
            # flavor_name = 'medium'
            )

        self.vnf2 = self.dc2.startCompute(
            'vnf2',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.2/24'}]
            # flavor_name = 'medium'
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
