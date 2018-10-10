import logging
import requests
from flask_restful import Resource
from json import loads, dumps

LOG = logging.getLogger("aro.endpoint.vim-ryu")
LOG.setLevel(logging.DEBUG)

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

API = "http://127.0.0.1:8080"
#/aro/ryu/links/

class WIMRyu(Resource):
    def get(self):
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            wim = self._switches(), self._links()
            return { 'WIM' : wim }
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def _switches(self):
        global API
        ## getting swicth info from ryu controller via rest
        rest_ryu_uri = API + "/aro/ryu/" + "switches/"
        req = requests.get(rest_ryu_uri)
        if req.status_code == 200:
            switches_dict = { 'switches ': req.json() }
            ## creating txt file to write the switch dict
            # with open('aro_out.txt', 'w') as f:
            #     print >> f, dumps(switches_dict, indent=4, sort_keys=True)
            # print(dumps(switches_dict, indent=4, sort_keys=True))
            return switches_dict
        else:
            raise Exception ("Ryu REST is not working for switches")

    def _links(self):
        global API
        ## getting swicth info from ryu controller via rest
        rest_ryu_uri = API + "/aro/ryu/" + "links/"
        req = requests.get(rest_ryu_uri)
        if req.status_code == 200:
            links_dict = { 'links ': req.json() }
            ## creating txt file to write the switch dict
            # with open('aro_out.txt', 'w') as f:
            #     print >> f, dumps(switches_dict, indent=4, sort_keys=True)
            # print(dumps(switches_dict, indent=4, sort_keys=True))
            return links_dict
        else:
            raise Exception ("Ryu REST is not working for links")


# dumps(self.wimdict, indent=4, sort_keys=True)
