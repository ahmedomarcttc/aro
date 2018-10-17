# aro
ARO Project

For placement engine

Changes to net.py

***def addLink(self, node1, node2, **params):

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

****

Changes to node.py
