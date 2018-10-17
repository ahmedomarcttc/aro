import logging
from flask_restful import Resource
from flask import request

LOG = logging.getLogger("aro.endpoint.vim")
LOG.setLevel(logging.DEBUG)

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

dcs = {}

def vim():
    return dcs

class Hosts(Resource):
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

class VIM(Resource):
    def get(self):
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        status = {}
        try:
            for dckey, dcvalue in vim().iteritems():
                vnfs = [vnf.name for vnf in dcvalue.containers.itervalues()]
                status.update({ dckey : vnfs })
            return status
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER
