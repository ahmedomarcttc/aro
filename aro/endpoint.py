
import logging
import threading
from flask import Flask
from flask_restful import Api
from gevent.pywsgi import WSGIServer

import wim
from wim import WIM, Switches, Links

from wim_ryu import WIMRyu

import vim
from vim import VIM, Hosts

LOG = logging.getLogger("aro.endpoint")
LOG.setLevel(logging.DEBUG)

class Endpoint(object):
    """
    Simple API endpoint that offers a REST interface.
    """

    def __init__(self, listenip, port, DCnetwork=None):
        self.ip = listenip
        self.port = port

        self.connectWIM(DCnetwork)

        self.app = Flask(__name__)
        self.api = Api(self.app)
        LOG.info("Created ARO API endpoint {}({}:{})".format(
            self.__class__.__name__, self.ip, self.port))

        self.api.add_resource(WIM, "/aro/wim")
        self.api.add_resource(Switches, "/aro/switches")
        self.api.add_resource(Links, "/aro/links")

        self.api.add_resource(WIMRyu, "/aro-ryu/wim")

        self.api.add_resource(VIM, "/aro/vim")
        self.api.add_resource(Hosts, "/aro/hosts")

    def connectWIM(self, net):
        wim.net = net
        LOG.info("Connected WIMNetwork to API endpoint {}({}:{})".format(
            self.__class__.__name__, self.ip, self.port))

    def connectVIM(self, dc):
        vim.dcs[dc.label] = dc
        LOG.info("Connected DC({}) to API endpoint {}({}:{})".format(
            dc.label, self.__class__.__name__, self.ip, self.port))

    def start(self):
        self.thread = threading.Thread(target=self._start_flask, args=())
        self.thread.daemon = True
        self.thread.start()
        LOG.info("Started API endpoint @ http://{}:{}".format(
            self.ip, self.port))

    def stop(self):
        if self.http_server:
            self.http_server.close()

    def _start_flask(self):
        # self.app.run(self.ip, self.port, debug=False, use_reloader=False)
        # this should be a more production-fit http-server
        # self.app.logger.setLevel(logging.ERROR)
        self.http_server = WSGIServer((self.ip, self.port), self.app,
                                      # This disables HTTP request logs to not
                                      # mess up the CLI when e.g. the
                                      # auto-updated dashboard is used
                                      log=open("/dev/null", "w")
                                      )
        self.http_server.serve_forever()
