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

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.lib import dpid as dpid_lib
from ryu.topology.api import get_switch, get_link

class StateTopologyController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(StateTopologyController, self).__init__(req, link, data, **config)
        self.app = data['topology_api_app']

    @route('topology', '/topology', methods=['GET'])
    def list_switches(self, req, **kwargs):
        body = json.dumps(self.app.topology)
        return Response(content_type='application/json', body=body)

    @route('flows', '/flows', methods=['GET'])
    def list_flows(self, req, **kwargs):
        body = json.dumps(self.app.flows)
        return Response(content_type='application/json', body=body)

    @route('port_stats', '/ports', methods=['GET'])
    def list_flows(self, req, **kwargs):
        body = json.dumps(self.app.flows)
        return Response(content_type='application/json', body=body)
        