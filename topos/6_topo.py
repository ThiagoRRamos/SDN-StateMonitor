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

        s1 = self.addSwitch('s1', ip='161.24.0.1/24', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', ip='161.24.0.2/24', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', ip='161.24.0.3/24', protocols='OpenFlow13')
        s4 = self.addSwitch('s4', ip='161.24.0.4/24', protocols='OpenFlow13')
        s5 = self.addSwitch('s5', ip='161.24.0.5/24', protocols='OpenFlow13')
        s6 = self.addSwitch('s6', ip='161.24.0.6/24', protocols='OpenFlow13')

    	hs = [self.addHost('h%d' % (x+1), ip='161.24.0.%d/24' % (x+7)) for x in xrange(6)]
        ss = [s1, s2, s3, s4, s5, s6]

        self.addLink(s1, s2, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s1, s4, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s2, s3, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s2, s4, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
    	self.addLink(s2, s5, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s3, s5, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s3, s6, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s4, s5, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s5, s6, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)

        for h, s in zip(hs, ss):
            self.addLink(h, s, delay='0ms', loss=0)

def topoTest():
    "Create network and run simple performance test"
    topo = ITATopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.interact()

if __name__ == '__main__':
    setLogLevel('info')
    topoTest()
