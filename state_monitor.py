import logging
import struct
import pprint
import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, tcp, udp, lldp
from ryu.lib import hub
from ryu.lib import addrconv

from latency_monitor import LatencyMonitorPacket

MAX32BITS = 1 << 31

# Always rx first

class LinkStats(object):

    def __init__(self):
        self.bw = 0.0
        self.latency = 0.0
        self.drop = 0.0

        self.cumulative_tx = {'packets': 0, 'errors': 0, 'bytes': 0, 'dropped': 0}
        self.speed_tx = {'packets': 0, 'errors': 0, 'bytes': 0, 'dropped': 0}
        self.cumulative_rx = {
            'errors': 0,'packets': 0, 'bytes': 0, 'crc_err': 0,
            'over_err': 0, 'dropped': 0, 'frame_err': 0}
        self.speed_rx = {
            'errors': 0,'packets': 0, 'bytes': 0, 'crc_err': 0,
            'over_err': 0, 'dropped': 0, 'frame_err': 0}

        self.last_update = time.time()

    def __str__(self):
        return "Stats: {:>8.2f} {:>8.2f} {:>8.2f} - {:>5.2f}".format(
            self.speed_rx['bytes'], self.speed_tx['bytes'], self.latency, self.last_update)

    def __repr__(self):
        return "LinkStats({}, {}, {})".format(self.speed_rx, self.speed_tx, self.last_update)

    def update(self, cumulative_rx, cumulative_tx):
        now = time.time()
        self.speed_rx = {p: (cumulative_rx[p] - self.cumulative_rx[p])/(now - self.last_update) for p in cumulative_rx}
        self.cumulative_rx.update(cumulative_rx)
        self.speed_tx = {p: (cumulative_tx[p] - self.cumulative_tx[p])/(now - self.last_update) for p in cumulative_tx}
        self.cumulative_tx.update(cumulative_tx)
        self.last_update = now


class StateLearner(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(StateLearner, self).__init__(*args, **kwargs)
        self.monitor_thread = hub.spawn(self._monitor)
        self.printer_thread = hub.spawn(self._printer)
        self._latency_thread = hub.spawn(self._latency_monitor)
        self.changed_flows = True

        self.mac_to_port = {}
        self.datapaths = {}
        self.topology = {}
        self.last_request = {}
        self.controller_link_latency = {}
        self.flows = {}

    # Methods called by the hubs

    def send_latency_message(self, dp, port):
        a = time.time()
        pkt = packet.Packet()
        lmp = LatencyMonitorPacket(dp.id, a, port)
        pkt.add_protocol(lmp)
        pkt.serialize()
        actions = [dp.ofproto_parser.OFPActionOutput(port)]
        out = dp.ofproto_parser.OFPPacketOut(
            datapath=dp, in_port=dp.ofproto.OFPP_CONTROLLER,
            buffer_id=dp.ofproto.OFP_NO_BUFFER, actions=actions,
            data=pkt.data)
        dp.send_msg(out)

    def _latency_monitor(self):
        while True:
            for dp in self.datapaths:
                for port in self.topology[dp]:
                    self.send_latency_message(self.datapaths[dp], port)
            hub.sleep(15)

    def _printer(self):
        pp = pprint.PrettyPrinter()
        while True:
            if self.changed_flows:
                self.changed_flows = False
                pp.pprint(self.flows)
            for dp in self.topology:
                for port in self.topology[dp]:
                    print "{:>3d} {:>11d}".format(dp, port), self.topology[dp][port][1]
            hub.sleep(10)

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_port_stats(dp)
            hub.sleep(15)

    def _request_port_stats(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.last_request[datapath.id] = time.time()
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # App handlers

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        src = msg.match.get('eth_src')
        dst = msg.match.get('eth_dst')
        dpid = msg.datapath.id
        self.changed_flows = True
        self.logger.info("Flow removed in %d from %s to %s", dpid, src, dst)
        if src and dst:
            if src not in self.flows:
                self.flows[src] = {}
            if dst not in self.flows[src]:
                self.flows[src][dst] = {}
            if dpid not in self.flows[src][dst]:
                self.flows[src][dst][dpid] = 0
            self.flows[src][dst][dpid] += msg.byte_count

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        latency = (time.time() - self.last_request[dpid])/2
        self.controller_link_latency[dpid] = latency
        for port in body:
            tx = {p[3:] : getattr(port, p) for p in dir(port) if p.startswith('tx')}
            rx = {p[3:] : getattr(port, p) for p in dir(port) if p.startswith('rx')}
            port_stats = self.topology[dpid][port.port_no][1]
            port_stats.update(rx,tx)

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def _port_desc_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.logger.info("Received ports descriptions from dp %d", dpid)
        for p in body:
            self.topology[dpid][p.port_no][1].bw = p.curr_speed

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
                self.topology[datapath.id] = {}
                for port in datapath.ports:
                    self.topology[datapath.id][port] = [datapath.ports[port], LinkStats(), 0, 0]
                req = parser.OFPPortDescStatsRequest(datapath, 0)
                datapath.send_msg(req)
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
                del self.topology[datapath.id]

    def add_flow(self, datapath, src, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(eth_src=src,
                                                 eth_dst=dst)
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, cookie=0, cookie_mask=0, table_id=0,
            command=ofproto.OFPFC_ADD, idle_timeout=10, hard_timeout=30,
            priority=0, buffer_id=ofproto.OFP_NO_BUFFER,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            flags=ofproto_v1_3.OFPFF_SEND_FLOW_REM, match=match, instructions=inst)
        datapath.send_msg(mod)

    def process_latency_packet(self, msg):
        a = LatencyMonitorPacket.parser(msg.data)
        dpid = msg.datapath.id
        in_port = msg.match['in_port']
        latency = time.time() - a.time
        if dpid in self.controller_link_latency:
            latency -= self.controller_link_latency[dpid]
        if a.dp in self.controller_link_latency:
            latency -= self.controller_link_latency[a.dp]
        self.topology[a.dp][a.port][1].latency = latency
        self.topology[a.dp][a.port][2] = dpid
        self.topology[a.dp][a.port][3] = in_port

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype == 0x0888:
            self.process_latency_packet(msg)
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

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, src, dst, actions)

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions)
        datapath.send_msg(out)
