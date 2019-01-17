import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork

from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint

from emuvim.api.aro.arorm import ARORM

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

EXTSWDPID_BASE = 100

class topo(DCNetwork):
    def __init__(self):
        super(topo, self).__init__(
            monitor=False,
            enable_learning=True
        )
        # define members for later use
        self.pop1 = None
        self.pop2 = None
        self.pop3 = None
        self.pop4 = None
        self.sw1 = None
        self.sw2 = None
        self.vnf1 = None
        self.vnf2 = None
        self.api_OS = []

    def _get_next_dpid(self):
        global EXTSWDPID_BASE
        EXTSWDPID_BASE += 1
        return EXTSWDPID_BASE

    def _create_switches(self):
        self.sw1 = self.addSwitch("sw1",
                                  mac = '00:00:00:00:00:01',
                                  dpid=hex(self._get_next_dpid())[2:])
        self.sw2 = self.addSwitch("sw2",
                                  mac = '00:00:00:00:00:02',
                                  dpid=hex(self._get_next_dpid())[2:])

    def _create_RM(self, cpu, ram):
        return ARORM(max_cu=cpu, max_mu=ram)

    def _create_pops(self):
        self.pop1 = self.addDatacenter("pop1")
        for sw in self.pop1.switch:
            self.pop1.assignResourceModeltoSw(self._create_RM(4, 1024), sw)

        self.pop2 = self.addDatacenter("pop2", topo='star', sw_param=3)
        for sw in self.pop2.switch:
            self.pop2.assignResourceModeltoSw(self._create_RM(4, 1024), sw)

        self.pop3 = self.addDatacenter("pop3", topo='mesh', sw_param=3)
        for sw in self.pop3.switch:
            self.pop3.assignResourceModeltoSw(self._create_RM(4, 1024), sw)

        self.pop4 = self.addDatacenter("pop4", topo='grid', sw_param=[3,4])
        for sw in self.pop4.switch:
            self.pop4.assignResourceModeltoSw(self._create_RM(4, 1024), sw)

    def _create_links(self):
        self.addLink(self.sw1, self.sw2)
        self.addLink(self.pop1, self.sw1)
        self.addLink(self.pop2, self.sw1)
        self.addLink(self.pop3, self.sw2)
        self.addLink(self.pop4, self.sw2)

    def testvnf(self):
        self.vnf1 = self.pop2.startCompute("vnf1", network=[{'id':'intf1', 'ip':'10.0.10.1/24'}])
        self.vnf2 = self.pop3.startCompute("vnf2", network=[{'id':'intf1', 'ip':'10.0.10.2/24'}])

    def _create_openstack_api_endpoints(self):
        # create
        for i in range(4): #range the number of DCs created
            self.api_OS.append(OpenstackApiEndpoint("172.31.255.1", 6001+i))
            self.api_OS[i].connect_dc_network(self)

        self.api_OS[0].connect_datacenter(self.pop1)
        self.api_OS[1].connect_datacenter(self.pop2)
        self.api_OS[2].connect_datacenter(self.pop3)
        self.api_OS[3].connect_datacenter(self.pop4)

    def create_topology(self):
        self._create_switches()
        self._create_pops()
        self._create_links()
        self._create_openstack_api_endpoints()
        self.testvnf()


    def start_topology(self):
        for api in self.api_OS:
            api.start()
        self.start()
        self.setChain('vnf1', 'vnf2', 'intf1', 'intf1', cmd='add-flow', bidirectional=True)


    def stop_topology(self):
        for api in self.api_OS:
            api.stop()
        self.stop()

def main():
    t = topo()
    t.create_topology()
    t.start_topology()
    t.CLI()
    t.stop_topology()

if __name__ == '__main__':
    main()
