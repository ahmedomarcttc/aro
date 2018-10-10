import logging
from flask_restful import Resource
from flask import request

LOG = logging.getLogger("aro.endpoint.vim")
LOG.setLevel(logging.DEBUG)

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

dcs = {}

def switchselector(dcname):
    global dcs
    print('this is {} with switches {}'.format(dcs[dcname].name, dcs[dcname].switch))
    return dcs[dcname].switch

def vim():
    return dcs

class VIM(Resource):
    def get(self):
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        status = {}
        try:
            for dckey, dcvalue in vim().iteritems():
                for vnfkey, vnfvalue in dcvalue.containers.iteritems():
                    status.update({ '{} status'.format(vnfkey) : vnfvalue.getStatus() })
            return status
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

class Hosts(Resource):
    pass
