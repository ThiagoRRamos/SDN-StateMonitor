import logging
import struct
import pprint
import time
import heapq
from collections import deque

from ryu.app.wsgi import WSGIApplication
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
from ryu.lib import stplib


from controller import StateTopologyController
from latency_monitor import LatencyMonitorPacket
import decision_maker as dm

MAX32BITS = 1 << 31

# Always rx first

class LinkStats(object):

    def __init__(self):
        self.bw = 0.0
        self.latency = None
        self.last_latency = 0.0
        self.drop = 0.0
        self.jitter = 0.0
        self.jitter_countdown = 4

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
        return "Stats: {:>8.2f} {:>8.2f} {:>8.2f} {:>6.3f}".format(
            self.speed_rx['bytes'], self.speed_tx['bytes'], self.latency, self.jitter)

    def __repr__(self):
        return "LinkStats({}, {}, {})".format(self.latency, self.jitter, self.speed_tx['bytes'])

    def update(self, cumulative_rx, cumulative_tx):
        now = time.time()
        self.speed_rx = {p: (cumulative_rx[p] - self.cumulative_rx[p])/(now - self.last_update) for p in cumulative_rx}
        self.cumulative_rx.update(cumulative_rx)
        self.speed_tx = {p: (cumulative_tx[p] - self.cumulative_tx[p])/(now - self.last_update) for p in cumulative_tx}
        self.cumulative_tx.update(cumulative_tx)
        self.last_update = now

    def add_latency(self, latency):
        if self.jitter_countdown > 0:
            self.jitter_countdown -= 1
        else:
            self.jitter = self.jitter + (abs(latency - self.last_latency) - self.jitter)/16.0
        self.last_latency = latency
        if self.latency is None:
            self.latency = latency
        else:
            self.latency = (latency + self.latency)/2

class StateLearner(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'wsgi': WSGIApplication,
    }

    def __init__(self, *args, **kwargs):
        super(StateLearner, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)

        wsgi = kwargs['wsgi']
        wsgi.register(StateTopologyController, {'topology_api_app': self})
        self.criteria = 4

        self.monitor_thread = hub.spawn(self._monitor)
        self.latency_thread = hub.spawn(self._latency_monitor)

        self.mac_to_port = {} #Standard Learning Switch structure, to tell which port is related to that mac
        self.closest_dpid = {} #Which dp is the first to receive messages from that mac
        self.datapaths = {} #List of datapaths
        self.topology = {} #Topology of datapaths

        self.last_request = {} #The last time in which the controller made a request to that switch
        self.controller_link_latency = {} #Latency between controller and switch
        
        self.flows = {} #Stats aggregated by type of flow
        self.ports_stats = {} #Stats aggregated by port

        self.updated_st = False
        self.st_ignored_ports = {} #Ports to be ignored on floods, in order to avod cycles

    # Hub helpers

    def send_latency_message(self, dp, port):
        pkt = packet.Packet()
        lmp = LatencyMonitorPacket(dp.id, time.time(), port)
        pkt.add_protocol(lmp)
        pkt.serialize()
        actions = [dp.ofproto_parser.OFPActionOutput(port)]
        out = dp.ofproto_parser.OFPPacketOut(
            datapath=dp, in_port=dp.ofproto.OFPP_CONTROLLER,
            buffer_id=dp.ofproto.OFP_NO_BUFFER, actions=actions,
            data=pkt.data)
        dp.send_msg(out)

    def _request_port_stats(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.last_request[datapath.id] = time.time()
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # Methods called by the hubs

    def send_latency_messages(self, dp=None):
        if dp is None:
            dps = list(self.datapaths.keys())
            for dp in dps:
                try:
                    for port in self.ports_stats[dp]:
                        self.send_latency_message(self.datapaths[dp], port)
                except:
                    pass
        else:
            for port in self.ports_stats[dp]:
                self.send_latency_message(self.datapaths[dp], port)

    def _latency_monitor(self):
        while True:
            try:
                self.send_latency_messages()
                hub.sleep(3)
                if not self.updated_st:
                    self.calculate_spanning_tree()
                hub.sleep(2)
            except:
                self.logger.info("Error in latency monitor")

    def _monitor(self):
        while True:
            try:
                for dp in self.datapaths.values():
                    self._request_port_stats(dp)
                hub.sleep(15)
            except:
                self.logger.info("Error in monitor")

    # App handlers

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        src = msg.match.get('eth_src')
        dst = msg.match.get('eth_dst')
        dpid = msg.datapath.id
        self.logger.debug("Flow removed in %d from %s to %s", dpid, src, dst)
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
            port_stats = self.ports_stats[dpid][port.port_no][1]
            port_stats.update(rx,tx)

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def _port_desc_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.logger.info("Received ports descriptions from dp %d", dpid)
        for p in body:
            self.ports_stats[dpid][p.port_no][1].bw = p.curr_speed

    def calculate_spanning_tree(self):
        self.updated_st = True
        if not self.datapaths:
            self.st_ignored_ports = {}
            return
        result = {}
        visited = set()
        frontier = deque()
        root = list(self.datapaths.keys())[0]
        frontier.append((root, None))
        deb = {}
        while frontier:
            els_in_frontier = [x[0] for x in frontier]
            el, parent = frontier.popleft()
            neighbors = self.topology[el]
            for neigh in neighbors:
                if neigh != parent:
                    if neigh in visited or neigh in els_in_frontier:
                        result.setdefault(el, set()).add(self.topology[el][neigh])
                        deb.setdefault(el, set()).add(neigh)
                        result.setdefault(neigh, set()).add(self.topology[neigh][el])
                        deb.setdefault(neigh, set()).add(el)
                    else:
                        frontier.append((neigh, el))
            visited.add(el)
        ports_ignored = sum(len(result[x]) for x in result)
        self.logger.info("Changed spanning tree. %d ports ignored" % ports_ignored)
        self.st_ignored_ports = result

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                dpid = datapath.id
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[dpid] = datapath
                self.ports_stats[dpid] = {}
                self.topology[dpid] = {}
                for port in datapath.ports:
                    self.ports_stats[datapath.id][port] = [datapath.ports[port], LinkStats(), None, None]
                req = parser.OFPPortDescStatsRequest(datapath, 0)
                datapath.send_msg(req)
                self.send_latency_messages(dpid)
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                try:
                    del self.datapaths[datapath.id]
                except KeyError:
                    pass
                try:
                    del self.topology[datapath.id]  
                except KeyError:
                    pass
                try:
                    del self.ports_stats[datapath.id]
                except KeyError:
                    pass
                try:
                    del self.mac_to_port[datapath.id]
                except KeyError:
                    pass
                closests = [k for k in self.closest_dpid if self.closest_dpid[k] == datapath.id]
                for c in closests:
                    del self.closest_dpid[c]
                try:
                    del self.last_request[datapath.id]
                except KeyError:
                    pass
                try:
                    del self.controller_link_latency[datapath.id]
                except KeyError:
                    pass
        self.updated_st = False

    def neighbors(self, a):
        try:
            neigh_map = self.ports_stats[a]
            for port in neigh_map:
                n = neigh_map[port]
                if n[2] and n[2] in self.topology[a]:
                    yield n, n[2]
        except:
            pass


    def path(self, parents, dst, src):
        a = []
        el = dst
        while el != src:
            a.append(el)
            el = parents[el]
        a.append(src)
        return list(reversed(a))

    def get_criteria(self, val=None):
        if val is None:
            val = self.criteria
        if val == 0:
            return dm.packet_loss
        if val == 1:
            return dm.available_speed
        if val == 2:
            return dm.jitter
        if val == 3:
            return dm.latency
        return dm.hops

    def decide_best_path(self, src_dpid, dst_mac, func):
        dst_dpid = self.closest_dpid.get(dst_mac)
        if not dst_dpid or src_dpid == dst_dpid:
            return None
        return self.do_decide_best_path(src_dpid, dst_dpid, func)
        
    def do_decide_best_path(self, src_dpid, dst_dpid, func):
        values = {src_dpid: 0.0}
        parent = {src_dpid: None}
        frontier = [(0, src_dpid)]
        while frontier:
            val, el = heapq.heappop(frontier)
            if dst_dpid in values and values[dst_dpid] <= val:
                return self.path(parent, dst_dpid, src_dpid)
            for link, neigh in self.neighbors(el):
                new_val = val + func(val, self.ports_stats, link)
                if neigh not in values or values[neigh] > new_val:
                    heapq.heappush(frontier, (new_val, neigh))
                    values[neigh] = new_val
                    parent[neigh] = el
        return None

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
        self.logger.debug("Adding flow on %d" % datapath.id)

    def process_latency_packet(self, msg):
        pkt_in = LatencyMonitorPacket.parser(msg.data)
        dpid = msg.datapath.id
        in_port = msg.match['in_port']
        latency = time.time() - pkt_in.time
        if dpid in self.controller_link_latency:
           latency -= self.controller_link_latency[dpid]
        if pkt_in.dp in self.controller_link_latency:
           latency -= self.controller_link_latency[pkt_in.dp]
        if pkt_in.dp in self.ports_stats and pkt_in.port in self.ports_stats[pkt_in.dp]:
            self.ports_stats[pkt_in.dp][pkt_in.port][1].add_latency(latency)
            self.ports_stats[pkt_in.dp][pkt_in.port][2] = dpid
            self.ports_stats[pkt_in.dp][pkt_in.port][3] = in_port
        if pkt_in.dp not in self.topology[dpid]:
            self.topology.setdefault(dpid, {})[pkt_in.dp] = in_port
            self.topology.setdefault(pkt_in.dp, {})[dpid] = pkt_in.port
            self.updated_st = False

    def flood_ports(self, ofproto, dpid, in_port):
        ports = self.datapaths[dpid].ports.keys()
        ignored = self.st_ignored_ports.setdefault(dpid, set())
        return [x for x in ports if x not in ignored]

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype == LatencyMonitorPacket.ETH_TYPE:
            self.process_latency_packet(msg)
            return
        dst = eth.dst
        src = eth.src

        if src not in self.closest_dpid:
            self.logger.debug("%s closest to %d" % (src, datapath.id))
            self.closest_dpid[src] = datapath.id

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port
        should_add_flow = False
        self.logger.debug("Packet in on %d to %s (%x)" % (dpid, dst, eth.ethertype))
        if dst in self.mac_to_port[dpid]:
            should_add_flow = True
            self.logger.debug("Decided via learning")
            ports = [self.mac_to_port[dpid][dst]]
        else:
            self.logger.debug("Flooding!")
            should_add_flow = (eth.ethertype == 0x806 and dst == "ff:ff:ff:ff:ff:ff")
            ports = self.flood_ports(ofproto, dpid, in_port)
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port) for out_port in ports]

        if should_add_flow:
            self.add_flow(datapath, src, dst, actions)
        
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions)
        datapath.send_msg(out)
