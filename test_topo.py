#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink, TCIntf
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

class ITATopo(Topo):

    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        switch_left = self.addSwitch('s1', ip='161.24.0.1/24', protocols='OpenFlow13')
        switch_center = self.addSwitch('s2', ip='161.24.0.2/24', protocols='OpenFlow13')
        switch_right = self.addSwitch('s3', ip='161.24.0.3/24', protocols='OpenFlow13')

    	h0 = self.addHost('h0', ip='161.24.0.4/24')
    	h1 = self.addHost('h1', ip='161.24.0.5/24')
        h2 = self.addHost('h2', ip='161.24.0.6/24')
        h3 = self.addHost('h3', ip='161.24.0.7/24')
        h4 = self.addHost('h4', ip='161.24.0.8/24')
        h5 = self.addHost('h5', ip='161.24.0.9/24')

        switches = [switch_left, switch_center, switch_right]
        hs = [h0, h1, h2, h3, h4, h5]

    	self.addLink(
            switch_left, switch_center,
            bw=10, delay='5ms', loss=1, max_queue_size=1000, use_htb=True)
    	self.addLink(
            switch_center, switch_right,
            bw=10, delay='5ms', loss=1, max_queue_size=1000, use_htb=True)
        for n, sw in enumerate(switches):
            self.addLink(
                sw, hs[2 * n],
                bw=10, delay='5ms', loss=2, max_queue_size=1000, use_htb=True)
            self.addLink(
                sw, hs[2 * n + 1],
                bw=10, delay='5ms', loss=2, max_queue_size=1000, use_htb=True)

def topoTest():
    "Create network and run simple performance test"
    topo = ITATopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.interact()

if __name__ == '__main__':
    setLogLevel('info')
    topoTest()
