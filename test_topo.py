import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.aro.endpoint import Endpoint

logging.basicConfig(level=logging.INFO)
setLogLevel('info')

EXTSWDPID_BASE = 100

class Topology(DCNetwork):
    """
    Topology with 2 switches and 2 datacenters:
        dc1 <--> sw1 <--> sw2 <--> dc2
    """
    def __init__(self):
        """
        Initialize multi PoP emulator network.
        """
        super(Topology, self).__init__(
            monitor=False,
            enable_learning=True
        )
        # define members for later use
        self.dc1 = None
        self.dc2 = None
        self.sw1 = None
        self.sw2 = None

    def _get_next_dpid(self):
        global EXTSWDPID_BASE
        EXTSWDPID_BASE += 1
        return EXTSWDPID_BASE

    def setup_topo(self):
        self._create_dcs()
        self._create_switches()
        self._create_links()
        # self._connect_openstack()
        # self._connect_restapi()
        self._connect_aro()
        self._create_hostvnf()

    def _create_dcs(self):
        self.dc1 = self.addDatacenter("dc1")
        self.dc2 = self.addDatacenter("dc2", topo='star', numswitch=3)
        # self.dc3 = self.addDatacenter("dc3", topo='mesh', numswitch=3)

    def _create_switches(self):
        self.sw1 = self.addSwitch("sw1", dpid=hex(self._get_next_dpid())[2:])
        self.sw2 = self.addSwitch("sw2", dpid=hex(self._get_next_dpid())[2:])

    def _create_links(self):
        self.addLink(self.dc1, self.sw1)
        self.addLink(self.dc2, self.sw2)
        self.addLink(self.sw1, self.sw2)

    def _create_hostvnf(self):
        self.vnf1 = self.dc1.startCompute("vnf1", network=[{'id': 'intf1', 'ip': '10.0.10.1/24'}])
        self.vnf2 = self.dc2.startCompute("vnf2", network=[{'id': 'intf1', 'ip': '10.0.10.2/24'}])

    # def _connect_openstack():
    #     # add OpenStack-like APIs to the emulated DC
    #     self.api1 = OpenstackApiEndpoint("172.31.255.1", 6001)
    #     self.api1.connect_datacenter(self.dc1)
    #     self.api1.connect_dc_network(self)
    #
    #     self.api2 = OpenstackApiEndpoint("172.31.255.1", 6002)
    #     self.api2.connect_datacenter(self.dc2)
    #     self.api2.connect_dc_network(self)
    #
    # def _connect_restapi():
    #     # add the command line interface endpoint to the emulated DC (REST API)
    #     self.rapi1 = RestApiEndpoint("0.0.0.0", 5001)
    #     self.rapi1.connectDCNetwork(self)
    #     self.rapi1.connectDatacenter(self.dc1)
    #     self.rapi1.connectDatacenter(self.dc2)

    def _connect_aro(self):
        self.aro = Endpoint("0.0.0.0", 2284)
        self.aro.connectWIM(self)
        self.aro.connectVIM(self.dc1)
        self.aro.connectVIM(self.dc2)

    def start_topo(self):
        self.start()
        # self.api1.start()
        # self.api2.start()
        # self.rapi1.start()
        self.aro.start()


    def stop_topo(self):
        self.aro.stop()
        # self.rapi1.stop()
        # self.api1.stop()
        # self.api2.stop()
        self.stop()

def main():
    t = Topology()
    t.setup_topo()
    t.start_topo()
    t.CLI()
    t.stop_topo()

if __name__ == '__main__':
    main()
