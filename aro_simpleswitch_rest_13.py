

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology.event import EventSwitchEnter, EventLinkAdd, EventSwitchLeave
from ryu.topology.api import get_all_switch, get_all_link, get_switch, get_link

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
# Imports for wsgi server
import ast
from webob import Response
import json

"""
This class is responsible for REST communication
"""

simple_switch_instance_name = 'simple_switch_api_app'
url = "/aro/ryu/"

class RestHandler(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(RestHandler, self).__init__(req, link, data, **config)
        self.simple_switch_app = data[simple_switch_instance_name]

    @route('simpleswitch', url+"switches/", methods=['GET'])
    def list_switches(self, req, **kwargs):
        simple_switch = self.simple_switch_app

        body = json.dumps(simple_switch.topo_blueprint.get_switches_info())
        return Response(content_type='application/json', body=body)

    @route('simpleswitch', url+"links/", methods=['GET'])
    def list_links(self, req, **kwargs):
        simple_switch = self.simple_switch_app

        body = json.dumps(simple_switch.topo_blueprint.get_links_info())
        return Response(content_type='application/json', body=body)


class ARORYUController13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = { 'wsgi': WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(ARORYUController13, self).__init__(*args, **kwargs)
        # switch learning variable (dictionary)
        self.mac_to_port = {}
        # blueprint (switches and links) of the topology
        self.topo_blueprint = TopologyBlueprint()

        wsgi = kwargs['wsgi']
        wsgi.register(RestHandler, {simple_switch_instance_name : self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        self.logger.info('OFPSwitchFeatures received: '
                         '\n\tdatapath_id=%016x',
                         msg.datapath_id)

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(EventSwitchEnter)
    def handler_switch_enter(self, ev):
        self.logger.info("Switch detected")
        # print([switch.dp.id for switch in get_switch(self)])
        # print(get_switch(self, None)[0].dp.ports)
        # print(get_switch(self, None)[0].ports)
        # print(get_switch(self, None)[0].to_dict())
        self.topo_blueprint.topo_raw_switches = get_switch(self, None)
        # self.logger.info(self.topo_blueprint.print_switches())

    @set_ev_cls(EventLinkAdd)
    def handler_link_add(self, ev):
        self.logger.info("Link detected")
        self.topo_blueprint.topo_raw_links = get_link(self, None)
        # self.logger.info(self.topo_blueprint.print_links())

    @set_ev_cls(EventSwitchLeave, [MAIN_DISPATCHER, CONFIG_DISPATCHER, DEAD_DISPATCHER])
    def handler_switch_leave(self, ev):
        self.logger.info("Not tracking Switches, switch leaved.")

class TopologyBlueprint(object):
    def __init__(self, *args, **kwargs):
        self.topo_raw_switches = []
        self.topo_raw_links = []
        self.topo_switches = []
        self.topo_links = []

    def print_switches(self):
        # print(self.topo_raw_switches)
        self.topo_switches = [switch.dp.id for switch in self.topo_raw_switches]
        return self.topo_switches

    def print_links(self):
        # print(dir(self.topo_raw_links))
        print(dir(self.topo_raw_links))
        self.topo_links = [(link.src.dpid, {'port no':link.src.port_no, 'port name':link.src.name},
                            link.dst.dpid, {'port no':link.dst.port_no, 'port name':link.dst.name})
                            for link in self.topo_raw_links]
        # print(dir(link.src), dir(link.dst))
        # print(link.src.name, link.dst.name)
        return self.topo_links

    def diesect_switch(self):
        pass

    def get_switches_info(self):
        """
        Returns a list of switch dpids.
        The switches are learned when they are joined using dpid.
        :rtype : list
        """
        # sw_info_dict = {}

        # for sw in self.topo_raw_switches:
            # sw_info_dict.update(
            #     {
            #         sw.dp.ports[4294967294].name : {
            #             'dpid' : sw.dp.id,
            #             'mac address' : sw.dp.ports[4294967294].hw_addr,
            #             'active intf' : [swport.name for swkey, swport in sw.dp.ports.iteritems() if swkey != 4294967294 ]
            #         }
            #     }
            # ) #sw.dp.ports[4294967294].to_jsondict()
        # return sw_info_dict

        sw_info_list = []
        for sw in self.topo_raw_switches:
            sw_info_list.append(
                {
                    'name' : sw.dp.ports[4294967294].name,
                    'dpid' : sw.dp.id,
                    'mac address' : sw.dp.ports[4294967294].hw_addr,
                    'active intf' : [swport.name for swkey, swport in sw.dp.ports.iteritems() if swkey != 4294967294 ]
                    }
            )
        return sw_info_list

    def get_links_info(self):
        """
        Uses the built in __str__ function to print the links saved in the class `topo_raw_links`.
        Returns a list of link strings
        """
        out = []
        for l in self.topo_raw_links:
            out.append(#str(l.src.name).split('-')[0]
                {
                    'ep1' : {
                        'interface' : l.src.name,
                        'from node' : str(l.src.name).split('-')[0]
                    },
                    'ep2' : {
                        'interface' : l.dst.name,
                        'from node' : str(l.dst.name).split('-')[0]
                    }
                }
            )
        return out
