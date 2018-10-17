# aro
ARO Project

For placement engine

Changes to net.py

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
      # start Ryu controller with rest-API
      python_install_path = site.getsitepackages()[0]
      # ryu default learning switch
      # ryu_path = python_install_path + '/ryu/app/simple_switch_13.py'
      # custom learning switch that installs a default NORMAL action in the
      # ovs switches
      dir_path = os.path.dirname(os.path.realpath(__file__))
      ryu_path = dir_path + '/aro_simpleswitch_rest_13.py'#'/son_emu_simple_switch_13.py'
      ryu_path2 = python_install_path + '/ryu/app/ofctl_rest.py'
      # change the default Openflow controller port to 6653 (official IANA-assigned port number), as used by Mininet
      # Ryu still uses 6633 as default
      ryu_option = '--ofp-tcp-listen-port'
      ryu_of_port = '6653'
      ryu_option0 = '--observe-links'
      ryu_cmd = 'ryu-manager'
      FNULL = open("/tmp/ryu.log", 'w')
      if learning_switch:
          self.ryu_process = Popen(
              [ryu_cmd, ryu_option0, ryu_option, ryu_of_port, ryu_path, ryu_path2], stdout=FNULL, stderr=FNULL)
          LOG.debug('starting ryu-controller with {0}'.format(ryu_path))
          LOG.debug('starting ryu-controller with {0}'.format(ryu_path2))
      else:
          # no learning switch, but with rest api
          self.ryu_process = Popen(
              [ryu_cmd, ryu_path2, ryu_option, ryu_of_port], stdout=FNULL, stderr=FNULL)
          LOG.debug('starting ryu-controller with {0}'.format(ryu_path2))
      time.sleep(1)

Changes to node.py

    class EmulatorCompute(Docker):
      def __init__(
              self, name, dimage, **kwargs):
          self.datacenter = kwargs.get("datacenter")  # pointer to current DC
          self.flavor_name = kwargs.get("flavor_name")
          self.connected_sw = kwargs.get("connected_sw")
          LOG.debug("Starting compute instance %r in data center %r" %
                    (name, str(self.datacenter)))
          # call original Docker.__init__
          Docker.__init__(self, name, dimage, **kwargs)

      def getNetworkStatus(self):
          """
          Helper method to receive information about the virtual networks
          this compute instance is connected to.
          """
          # get all links and find dc switch interface
          networkStatusList = []
          for i in self.intfList():
              vnf_name = self.name
              vnf_interface = str(i)
              dc_port_name = self.datacenter.net.find_connected_dc_interface(
                  vnf_name, vnf_interface)
              connected_sw = self.connected_sw.name
              # format list of tuples (name, Ip, MAC, isUp, status, dc_portname)
              intf_dict = {'intf_name': str(i), 'ip': "{0}/{1}".format(i.IP(), i.prefixLen), 'netmask': i.prefixLen,
                           'mac': i.MAC(), 'up': i.isUp(), 'status': i.status(), 'dc_portname': dc_port_name,
                           'Connect to switch': connected_sw}
              networkStatusList.append(intf_dict)

          return networkStatusList

    class Datacenter(object):
        def __init__(self, label, metadata={}, resource_log_path=None):
            # first prototype assumes one "bigswitch" per DC
            self.switch = []
            self.gw = None
            # keep track of running containers
            self.containers = {}
            # keep track of attached external access points
            self.extSAPs = {}
            # pointer to assigned resource model
            self._resource_model = None


        def create(self):
            """
            Each data center is represented by a single switch to which
            compute resources can be connected at run time.

            TODO: This will be changed in the future to support multiple networks
            per data center
            """
            self.gw = self.net.addSwitch("%s.gw" % self.name, dpid=hex(self._get_next_dc_dpid())[2:])
            LOG.debug("created data center gateway: %s" % str(self.gw))

            self.switch.append(self.net.addSwitch("%s.s1" % self.name, dpid=hex(self._get_next_dc_dpid())[2:]))
            LOG.debug("created data center switch: %s" % str(self.switch))

            for switch in self.switch:
                LOG.debug("created data center switch: %s" % str(switch))
                self.net.addLink(self.gw, switch, cls=Link)

        def startCompute(self, name, image=None, command=None, network=None,
                         flavor_name="tiny", connected_sw=None, properties=dict(), **params):
            """
            Create a new container as compute resource and connect it to this
            data center.
            :param name: name (string)
            :param image: image name (string)
            :param command: command (string)
            :param network: networks list({"ip": "10.0.0.254/8"}, {"ip": "11.0.0.254/24"})
            :param flavor_name: name of the flavor for this compute container
            :param properties: dictionary of properties (key-value) that will be passed as environment variables
            :return:
            """
            assert name is not None
            # no duplications
            if name in [c.name for c in self.net.getAllContainers()]:
                raise Exception("Container with name %s already exists." % name)
            # set default parameter
            if image is None:
                image = "ubuntu:trusty"
            if network is None:
                network = {}  # {"ip": "10.0.0.254/8"}
            if isinstance(network, dict):
                # if we have only one network, put it in a list
                network = [network]
            if isinstance(network, list):
                if len(network) < 1:
                    network.append({})

            # apply hard-set resource limits=0
            cpu_percentage = params.get('cpu_percent')
            if cpu_percentage:
                params['cpu_period'] = self.net.cpu_period
                params['cpu_quota'] = self.net.cpu_period * float(cpu_percentage)

            env = properties
            properties['VNF_NAME'] = name

            if connected_sw is None:
                connected_sw = self.switch[0]
            # connected_sw = switchselector(self.name)

            # create the container
            d = self.net.addDocker(
                "%s" % (name),
                dimage=image,
                dcmd=command,
                datacenter=self,
                flavor_name=flavor_name,
                environment=env,
                connected_sw=connected_sw,
                **params
            )

            # apply resource limits to container if a resource model is defined
            if self._resource_model is not None:
                try:
                    self._resource_model.allocate(d)
                    self._resource_model.write_allocation_log(
                        d, self.resource_log_path)
                except NotEnoughResourcesAvailable as ex:
                    LOG.warning(
                        "Allocation of container %r was blocked by resource model." % name)
                    LOG.info(ex.message)
                    # ensure that we remove the container
                    self.net.removeDocker(name)
                    return None

            # connect all given networks
            # if no --net option is given, network = [{}], so 1 empty dict in the list
            # this results in 1 default interface with a default ip address
            for nw in network:
                # clean up network configuration (e.g. RTNETLINK does not allow ':'
                # in intf names
                if nw.get("id") is not None:
                    nw["id"] = self._clean_ifname(nw["id"])
                # TODO we cannot use TCLink here (see:
                # https://github.com/mpeuster/containernet/issues/3)
                self.net.addLink(d, d.connected_sw, params1=nw,
                                 cls=Link, intfName1=nw.get('id'))
            # do bookkeeping
            self.containers[name] = d

            return d  # we might use UUIDs for naming later on

        def stopCompute(self, name):
            """
            Stop and remove a container from this data center.
            """
            assert name is not None
            if name not in self.containers:
                raise Exception("Container with name %s not found." % name)
            LOG.debug("Stopping compute instance %r in data center %r" %
                      (name, str(self)))

            #  stop the monitored metrics
            if self.net.monitor_agent is not None:
                self.net.monitor_agent.stop_metric(name)

            # call resource model and free resources
            if self._resource_model is not None:
                self._resource_model.free(self.containers[name])
                self._resource_model.write_free_log(
                    self.containers[name], self.resource_log_path)

            # remove links
            self.net.removeLink(
                link=None, node1=self.containers[name], node2=self.containers[name].connected_sw)

            # remove container
            self.net.removeDocker("%s" % (name))
            del self.containers[name]

            return True

        def attachExternalSAP(self, sap_name, sap_net, **params):
            extSAP = EmulatorExtSAP(sap_name, sap_net, self, **params)
            # link SAP to the DC switch
            self.net.addLink(extSAP.switch, self.gw, cls=Link)
            self.extSAPs[sap_name] = extSAP

        def removeExternalSAP(self, sap_name):
            sap_switch = self.extSAPs[sap_name].switch
            # sap_switch = self.net.getNodeByName(sap_name)
            # remove link of SAP to the DC switch
            self.net.removeLink(link=None, node1=sap_switch, node2=self.gw)
            self.net.removeExtSAP(sap_name)
            del self.extSAPs[sap_name]

        def getStatus(self):
            """
            Return a dict with status information about this DC.
            """
            container_list = [name for name in self.containers]
            ext_saplist = [sap_name for sap_name in self.extSAPs]
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
