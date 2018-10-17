import logging

from random import choice
from vim import dcs

LOG = logging.getLogger("aro.placement")
LOG.setLevel(logging.DEBUG)


def switchselector(dcname):
    global dcs
    chosen_sw = choice(dcs[dcname].switch)
    LOG.info('From {} the {} switch was chosen'.format(dcs[dcname].name, chosen_sw))
    return chosen_sw

def placevnf(name, image=None, command=None, network=None, flavor_name=None, placement=None, properties=dict(), **params):
    if flavor_name is None:
        flavor_name = 'tiny'
    if placement is None:
        placement = FirstDC()
    dc = placement.place()
    connected_sw = switchselector(dc.name)
    vnf = dc.startCompute(name, image, command, network, flavor_name, connected_sw=connected_sw, properties=dict(), **params)
    return vnf


"""
Some (simple) placement algorithms
"""


class FirstDC(object):
    """
    Placement: Always use one and the same data center from the dcs dict.
    """

    def place(self):
        LOG.debug("Placement Algorithm: %s" % str(self.__class__.__name__))
        # for dckey, dcvalue in dcs.iteritems():
        dc = list(dcs.itervalues())[0]
        return dc

c = 0
class RoundRobinDC(object):
    """
    Placement: Distribute VNFs across all available DCs in a round robin fashion.
    """

    def place(self):
        LOG.debug("Placement Algorithm: %s" % str(self.__class__.__name__))
        global c
        dcs_list = list(dcs.itervalues())
        if c == len(dcs_list):
            c = 0
        dc = list(dcs.itervalues())[c]
        c += 1
        return dc


class RandomSelectDC(object):
        """
        Placement: Distribute VNFs across all available DCs in a random fashion.
        """

        def place(self):
            LOG.debug("Placement Algorithm: %s" % str(self.__class__.__name__))
            dcs_list = list(dcs.itervalues())
            return choice(dcs_list)
