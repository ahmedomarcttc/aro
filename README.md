# aro
## ARO Project

### For placement engine

###### Changes to net.py

```
def addDatacenter(self, label, topo=None, sw_param=None, metadata={}, resource_log_path=None):
    if label in self.dcs:
      raise Exception("Data center label already exists: %s" % label)
    dc = Datacenter(label, metadata=metadata, resource_log_path=resource_log_path)
    dc.net = self  # set reference to network
    self.dcs[label] = dc
    dc.create(topo, sw_param)  # finally create the data center in our Mininet instance
    LOG.info("added data center: %s" % label)
    return dc

def addLink(self, node1, node2, **params):
  # ensure type of node1
  if isinstance(node1, basestring):
      if node1 in self.dcs:
          node1 = self.dcs[node1].gw
  if isinstance(node1, Datacenter):
      node1 = node1.gw
  # ensure type of node2
  if isinstance(node2, basestring):
      if node2 in self.dcs:
          node2 = self.dcs[node2].gw
  if isinstance(node2, Datacenter):
      node2 = node2.gw
  # try to give containers a default IP

def startRyu(self, learning_switch=True):

  ## aro ryu paths
  ryu_path = dir_path + '/aro_simpleswitch_rest_13.py'
  ryu_option0 = '--observe-links'
  ryu_path2 = python_install_path + '/ryu/app/ofctl_rest.py'
  # change the default Openflow controller port to 6653 (official IANA-assigned port number), as used by Mininet
  # Ryu still uses 6633 as default
  ryu_option = '--ofp-tcp-listen-port'
  ryu_of_port = '6653'
  ryu_cmd = 'ryu-manager'
  FNULL = open("/tmp/ryu.log", 'w')
  if learning_switch:
      self.ryu_process = Popen(
          [ryu_cmd, ryu_option0, ryu_option, ryu_of_port, ryu_path, ryu_path2], stdout=FNULL, stderr=FNULL)
      LOG.debug('starting ryu-controller with {0}'.format(ryu_path))
      LOG.debug('starting ryu-controller with {0}'.format(ryu_path2))
```
###### Changes to node.py
```
class EmulatorCompute(Docker):
  def __init__(
          self, name, dimage, \**kwargs):
      self.datacenter = kwargs.get("datacenter")  # pointer to current DC
      self.flavor_name = kwargs.get("flavor_name")
      self.connected_sw = kwargs.get("connected_sw")
      LOG.debug("Starting compute instance %r in data center %r" %
                (name, str(self.datacenter)))
      # call original Docker.__init__
      Docker.__init__(self, name, dimage, \**kwargs)

  def getNetworkStatus(self):

          # format list of tuples (name, Ip, MAC, isUp, status, dc_portname)
          intf_dict = {'intf_name': str(i), 'ip': "{0}/{1}".format(i.IP(), i.prefixLen), 'netmask': i.prefixLen,
          'mac': i.MAC(), 'up': i.isUp(), 'status': i.status(), 'dc_portname': dc_port_name,
          'Connect to switch': self.connected_sw.name}

class Datacenter(object):

DC_COUNTER = 0
    def __init__(self, label, metadata={}, resource_log_path=None):
        .
        .
        .
        Datacenter.DC_COUNTER += 1
        self.name = "dc%d" % Datacenter.DC_COUNTER
        # creating unique dpid for switches
        self.DCDPID_BASE1 = 1000 * Datacenter.DC_COUNTER
        self.counter = 0
        # first prototype assumes one "bigswitch" per DC
        self.switch = []
        self.gw = None
        # pointer to assigned resource model
        self._resource_model = None
        #add RM to individual switches
        self._RM_switch = {}

    def _get_next_dc_dpid(self):
        self.counter += 1
        return self.DCDPID_BASE1 + self.counter

    def star_topo(self, numswitch):
        for i in range(numswitch):
            self.switch.append(self.net.addSwitch("{}.s{}".format(self.name, i+1), dpid=hex(self._get_next_dc_dpid())[2:]))
            LOG.debug("created data center switch: %s" % str(self.switch[i]))
            self._RM_switch[self.switch[i].name] = None
            self.net.addLink(self.gw, self.switch[i])

    def mesh_topo(self, numswitch):
        for i in range(numswitch):
            self.switch.append(self.net.addSwitch("{}.s{}".format(self.name, i+1), dpid=hex(self._get_next_dc_dpid())[2:]))
            LOG.debug("created data center switch: %s" % str(self.switch[i]))
            self._RM_switch[self.switch[i].name] = None
            self.net.addLink(self.gw, self.switch[i])
            for j in range(i):
                self.net.addLink(self.switch[j], self.switch[i])

    def grid_topo(self, grid_dim):
        for i in range(grid_dim[0]*grid_dim[1]):
            self.switch.append(self.net.addSwitch("{}.s{}".format(self.name, i+1), dpid=hex(self._get_next_dc_dpid())[2:]))
            LOG.debug("created data center switch: %s" % str(self.switch[i]))
            self._RM_switch[self.switch[i].name] = None
        for l in range(grid_dim[0]*grid_dim[1]):
            if l != ((grid_dim[0]*grid_dim[1])-1):
                if (l % grid_dim[0]) == (grid_dim[0] - 1):
                    self.net.addLink(self.switch[l], self.switch[l+grid_dim[0]])
                elif l >= (grid_dim[0]*(grid_dim[1] - 1)):
                    self.net.addLink(self.switch[l], self.switch[l+1])
                else:
                    self.net.addLink(self.switch[l], self.switch[l+grid_dim[0]])
                    self.net.addLink(self.switch[l], self.switch[l+1])
            else:
                self.net.addLink(self.gw, self.switch[l])

    def create(self, topo, sw_param):
        """
        Each data center is represented by a single switch to which
        compute resources can be connected at run time.

        TODO: This will be changed in the future to support multiple networks
        per data center
        """
        self.gw = self.net.addSwitch("%s.gw" % self.name, dpid=hex(self._get_next_dc_dpid())[2:])
        LOG.debug("created data center gateway switch: %s" % str(self.gw))

        if topo is 'star':
            self.star_topo(sw_param)
        elif topo == 'mesh':
            self.mesh_topo(sw_param)
        elif topo == 'grid':
            self.grid_topo(sw_param)
        else:
            self.switch.append(self.net.addSwitch("{}.s1".format(self.name), dpid=hex(self._get_next_dc_dpid())[2:]))
            LOG.debug("created data center switch: %s" % str(self.switch[0]))
            self._RM_switch[self.switch[0].name] = None
            self.net.addLink(self.gw, self.switch[0])

    def startCompute(self, name, image=None, command=None, network=None, flavor_name="tiny", conn_sw=None, properties=dict(), **params):
        .
        .
        .
        env = properties
        properties['VNF_NAME'] = name

        if conn_sw is None:
            conn_sw = self.switch[0]
        # conn_sw = switchselector(self.name)

        # create the container
        d = self.net.addDocker(
            "%s" % (name),
            dimage=image,
            dcmd=command,
            datacenter=self,
            flavor_name=flavor_name,
            environment=env,
            connected_sw=conn_sw,
            **params
        )
        .
        .
        .
        for nw in network:
            # clean up network configuration (e.g. RTNETLINK does not allow ':'
            # in intf names
            if nw.get("id") is not None:
                nw["id"] = self._clean_ifname(nw["id"])
            # TODO we cannot use TCLink here (see:
            # https://github.com/mpeuster/containernet/issues/3)
            self.net.addLink(d, d.connected_sw, params1=nw,
                             cls=Link, intfName1=nw.get('id'))


    def stopCompute(self, name):
        .
        .
        .
        # remove links
        self.net.removeLink(
            link=None, node1=self.containers[name], node2=self.containers[name].connected_sw)


    def attachExternalSAP(self, sap_name, sap_net, **params):

        self.net.addLink(extSAP.switch, self.gw, cls=Link)


    def removeExternalSAP(self, sap_name):

        self.net.removeLink(link=None, node1=sap_switch, node2=self.gw)


    def getStatus(self):

        return {
            "label": self.label,
            "internalname": self.name,
            "switch": [switch.name for switch in self.switch],
            "gateway" : self.gw.name,
            "n_running_containers": len(self.containers),
            "metadata": self.metadata,
            "vnf_list": container_list,
            "ext SAP list": ext_saplist
        }
```
