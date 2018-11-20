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
        # Creating unique dpid
        global EXTSWDPID_BASE
        EXTSWDPID_BASE += 1
        return EXTSWDPID_BASE

    def setup_topo(self):
        # Creating and configuring the Topology
        self._create_dcs()
        self._create_switches()
        self._create_links()
        self._create_hostvnf()
        self._connect_aro()

    def _create_RM(self, cpu, ram):
        # Creating resource models
        return ARORM(max_cu=cpu, max_mu=ram)

    def _create_dcs(self):
        # Creating Datacenter with resource models assigned to each switch.
        self.dc1 = self.addDatacenter("dc1")
        self.dc1.assignResourceModeltoSw(self._create_RM(8, 1024), self.dc1.switch[0].name)

        self.dc2 = self.addDatacenter("dc2", topo='star', sw_param=3)
        for sw in self.dc2.switch:
            self.dc2.assignResourceModeltoSw(self._create_RM(4, 1024), sw.name)

        self.dc3 = self.addDatacenter("dc3", topo='mesh', sw_param=3)
        for sw in self.dc3.switch:
            self.dc3.assignResourceModeltoSw(self._create_RM(8, 1024), sw.name)

        self.dc4 = self.addDatacenter("dc4", topo='grid', sw_param=[3,4])
        for sw in self.dc4.switch:
            self.dc4.assignResourceModeltoSw(self._create_RM(4, 1024), sw.name)
        # self.dc5 = self.addDatacenter("dc5", topo='tree', numswitch=3)

    def _create_switches(self):
        # Creating switches
        self.sw1 = self.addSwitch("sw1", dpid=hex(self._get_next_dpid())[2:])

    def _create_links(self):
        # Creating links
        self.addLink(self.dc1, self.sw1)
        self.addLink(self.dc2, self.sw1)
        self.addLink(self.dc3, self.sw1)
        self.addLink(self.dc4, self.sw1)

    def _create_hostvnf(self):
        # Creating dummy vnfs
        self.vnf1 = self.dc1.startCompute("vnf1", network=[{'id': 'intf1', 'ip': '10.0.10.1/24'}])
        self.vnf2 = self.dc2.startCompute("vnf2", network=[{'id': 'intf1', 'ip': '10.0.10.2/24'}], flavor_name = 'small')
        self.vnf3 = self.dc3.startCompute("vnf3", network=[{'id': 'intf1', 'ip': '10.0.10.3/24'}], flavor_name = 'medium')
        self.vnf4 = self.dc4.startCompute("vnf4", network=[{'id': 'intf1', 'ip': '10.0.10.4/24'}], flavor_name = 'large')

    def _connect_aro(self):
        # Adding to ARO api
        self.aro = Endpoint("0.0.0.0", 2284, DCnetwork=self)
        self.aro.connectVIM(self.dc1)
        self.aro.connectVIM(self.dc2)
        self.aro.connectVIM(self.dc3)
        self.aro.connectVIM(self.dc4)

    def start_topo(self):
        # Starting Topology
        self.start()
        self.aro.start()

    def stop_topo(self):
        # Stoping Topology
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
