import logging
from flask_restful import Resource

LOG = logging.getLogger("aro.endpoint.wim")
LOG.setLevel(logging.DEBUG)

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

net = None
wim_dict = {}

def wim():
    global wim_dict

    switches = []
    for switch in net.switches:
        switches.append(
            {
                'name' : switch.name,
                'dpid' : int(switch.dpid, 16),
                'active_intf': [str(k) for k, v in switch.ports.items() if str(k) != 'lo']
            }
        )
    wim_dict.update( { 'Switches' : switches } )

    links = []
    for link in net.links:
        links.append(
            {
                'ep1' : {
                    'interface': link.intf1.name,
                    'from node': link.intf1.node.name
                },
                'ep2' : {
                    'interface': link.intf2.name,
                    'from node': link.intf2.node.name
                }
            }
        )
    wim_dict.update( { 'Links' : links } )

    return wim_dict

class WIM(Resource):

    def get(self):
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            return wim()
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

class Switches(Resource):

    def get(self):
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            return wim()['Switches']
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

class Links(Resource):
    def get(self):
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            return wim()['Links']
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER
