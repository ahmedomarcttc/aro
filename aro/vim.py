import logging
from flask_restful import Resource
from flask import request

logging.basicConfig()

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
        logging.debug("API CALL: WIM")
        try:
            for dckey, dcvalue in vim().iteritems():
                # print(dir(dcvalue))
                print(dcvalue.containers)
                for vnfkey, vnfvalue in dcvalue.containers.iteritems():
                    print(dir(vnfvalue))
                    # print(vnfvalue)
                    return { 'get status' : vnfvalue.getStatus(),
                             'get net status' : vnfvalue.getNetworkStatus() }
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

class Hosts(Resource):
    pass
