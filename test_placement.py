import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint

from emuvim.api.aro.endpoint import Endpoint
from emuvim.api.aro.arorm import ARORM
from emuvim.api.aro.placement import FirstDC, RoundRobinDC, placevnf

logging.basicConfig(level=logging.INFO)
setLogLevel('info')  # set Mininet loglevel

logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.base').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.compute').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.keystone').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.nova').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.neutron').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.heat').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.heat.parser').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.glance').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.helper').setLevel(logging.DEBUG)


class Topology(DCNetwork):
    def __init__(self):
        super(Topology, self).__init__(
            monitor=False,
            enable_learning=True
        )

    def setup_topo(self):
        self._create_dcs()
        # self._create_switches()
        self._create_links()
        self._create_openstack_api_endpoints()
        self._connect_aro()
        # self._create_hostvnf()
        self._create_vnf()

    def _create_dcs(self):
        rm = ARORM(max_cu=32, max_mu=8192)

        self.dc1 = self.addDatacenter("dc1")
        self.dc1.assignResourceModel(rm)

        self.dc2 = self.addDatacenter("dc2")
        self.dc2.assignResourceModel(rm)

    def _create_links(self):
        self.addLink(self.dc1, self.dc2)

    def _create_hostvnf(self):
        self.hostvnf1 = self.dc1.startCompute(
            'hostvnf1',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.1/24'}],
            flavor_name = 'medium'
            )
        self.hostvnf2 = self.dc2.startCompute(
            'hostvnf2',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.2/24'}],
            flavor_name = 'medium'
            )

    def _create_vnf(self):
        placement = RoundRobinDC()

        self.vnf1 = placevnf(
            'vnf1',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.1/24'}],
            flavor_name = 'medium',
            placement = placement
            )
        self.vnf2 = placevnf(
            'vnf2',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.2/24'}],
            flavor_name = 'medium',
            placement = placement
            )
        self.vnf3 = placevnf(
            'vnf3',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.3/24'}],
            flavor_name = 'medium',
            placement = placement
            )
        self.vnf4 = placevnf(
            'vnf4',
            network = [{'id' : 'intf1', 'ip' : '10.0.10.4/24'}],
            flavor_name = 'medium',
            placement = placement
            )

    def _create_openstack_api_endpoints(self):
        self.api1 = OpenstackApiEndpoint("172.31.255.1", 6001)
        self.api1.connect_dc_network(self)
        self.api1.connect_datacenter(self.dc1)

        self.api2 = OpenstackApiEndpoint("172.31.255.1", 6002)
        self.api2.connect_dc_network(self)
        self.api2.connect_datacenter(self.dc2)

    def _connect_aro(self):
        self.aro = Endpoint("0.0.0.0", 2284, DCnetwork=self)
        self.aro.connectWIM()
        self.aro.connectVIM(self.dc1)
        self.aro.connectVIM(self.dc2)

    def start_topo(self):
        self.start()
        self.api1.start()
        self.api2.start()
        self.aro.start()

    def stop_topo(self):
        self.aro.stop()
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
