# Copyright (C) 2013 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

    @route('topology', '/json/topology', methods=['GET'])
    def json_switches(self, req, **kwargs):
        body = json.dumps(self.app.topology)
        return Response(content_type='application/json', body=body)

    @route('flows', '/json/flows', methods=['GET'])
    def json_flows(self, req, **kwargs):
        body = json.dumps(self.app.flows)
        return Response(content_type='application/json', body=body)

    @route('latencies', '/json/latencies', methods=['GET'])
    def json_latencies(self, req, **kwargs):
        latencies = {}
        for dpid in self.app.ports_stats:
            latencies[dpid] = {}
            for other_dpid in self.app.topology[dpid]:
                port = self.app.topology[dpid][other_dpid]
                print self.app.ports_stats[dpid][port]
                latencies[dpid][other_dpid] = self.app.ports_stats[dpid][port][1].latency
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