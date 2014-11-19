import json
from webob import Response

from html import HTML
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link

class StateTopologyController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(StateTopologyController, self).__init__(req, link, data, **config)
        self.app = data['topology_api_app']
        #self.logger.setLevel(49)

    @route('topology', '/json/topology', methods=['GET'])
    def json_switches(self, req, **kwargs):
        body = json.dumps(self.app.topology)
        return Response(content_type='application/json', body=body)

    @route('flows', '/json/flows', methods=['GET'])
    def json_flows(self, req, **kwargs):
        body = json.dumps(self.app.flows)
        return Response(content_type='application/json', body=body)

    @route('connection_information', '/json/link', methods=['GET'])
    def json_flows(self, req, **kwargs):
        origin = int(req.params.get('o'))
        destiny = int(req.params.get('d'))
        if destiny in self.app.topology[origin]:
            port = self.app.topology[origin][destiny]
            stats = self.app.ports_stats[origin][port][1]
            stx = stats.speed_tx
            ctx = stats.cumulative_tx
            sent1 = float(stats.cumulative_tx['packets'])
            received1 = float(stats.cumulative_rx['packets'])
            l1, j1 = stats.latency, stats.jitter
        if origin in self.app.topology[destiny]:
            port = self.app.topology[destiny][origin]
            stats = self.app.ports_stats[destiny][port][1]
            srx = stats.speed_rx
            crx = stats.cumulative_rx
            sent2 = float(stats.cumulative_tx['packets'])
            received2 = float(stats.cumulative_rx['packets'])
            l2, j2 = stats.latency, stats.jitter
        latency, jitter = l1 + l2, j1 + j2
        packet_loss1 = 1.0 - received2/sent1 if sent1 else 0.0
        packet_loss2 = 1.0 - received1/sent2 if sent2 else 0.0
        expected_round_loss = 1.0 - (1.0 - packet_loss1)*(1.0 - packet_loss2)
        body = json.dumps({"latency": latency, "jitter": jitter,
            "packet_loss": packet_loss1, "speed_tx": stx, "speed_rx": srx,
            "cumulative_tx": ctx, "cumulative_rx": crx, "round_loss": expected_round_loss})
        return Response(content_type='application/json', body=body + "\n")

    @route('latencies', '/json/latencies', methods=['GET'])
    def json_latencies(self, req, **kwargs):
        latencies = {}
        for dpid in self.app.ports_stats:
            latencies[dpid] = {}
            for other_dpid in self.app.topology[dpid]:
                port = self.app.topology[dpid][other_dpid]
                latencies[dpid][other_dpid] = self.app.ports_stats[dpid][port][1].latency
        body = json.dumps(latencies)
        return Response(content_type='application/json', body=body)

    @route('jitters', '/json/jitters', methods=['GET'])
    def json_jitters(self, req, **kwargs):
        latencies = {}
        for dpid in self.app.ports_stats:
            latencies[dpid] = {}
            for other_dpid in self.app.topology[dpid]:
                port = self.app.topology[dpid][other_dpid]
                latencies[dpid][other_dpid] = self.app.ports_stats[dpid][port][1].jitter
        body = json.dumps(latencies)
        return Response(content_type='application/json', body=body)

    @route('latencies', '/json/port_stats', methods=['GET'])
    def json_post_stats(self, req, **kwargs):
        body = json.dumps(self.app.ports_stats)
        return Response(content_type='application/json', body=body)

    @route('port_stats', '/port_stats', methods=['GET'])
    def port_stats(self, req, **kwargs):
        h = HTML()
        b = h.body
        table = b.table(border='1')
        headers = {'Latency': lambda x: x.latency,
            'Jitter': lambda x: x.jitter,
            "B/s sent": lambda x: x.speed_tx['bytes'],
            "Packets sent": lambda x: x.cumulative_tx['packets']}
        headers_order = ['Latency', 'Jitter', "B/s sent", "Packets sent"]
        trh = table.tr
        trh.th("Origin")
        trh.th("Destiny")
        for header in headers_order:
            trh.th(header)
        for dpid, port_data in self.app.ports_stats.items():
            for port, data in port_data.items():
                if data[2]:
                    tr = table.tr
                    tr.td(str(dpid))
                    tr.td(str(data[2]))
                    for header in headers_order:
                        func = headers[header]
                        tr.td("{:.3f}".format(func(data[1])))
        return Response(body=str(h))
       
    @route('paths', '/paths', methods=['GET'])    
    def decided_paths(reslf, req, **kwargs):
        h = HTML()
        b = h.body
        table = b.table(border='1')
        trh = table.tr
        trh.th("Datapath Origin")
        trh.th("Mac Destiny")
        for dp in datapaths:
            for mac in self.app.closest_dpid:
                pass
        return Response(body=str(h))