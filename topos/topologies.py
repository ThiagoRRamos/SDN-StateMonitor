from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink, TCIntf
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

from topo_utils import test_performance

class DenseTopo(Topo):

    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        s1 = self.addSwitch('s1', ip='161.24.0.1/24', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', ip='161.24.0.2/24', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', ip='161.24.0.3/24', protocols='OpenFlow13')
        s4 = self.addSwitch('s4', ip='161.24.0.4/24', protocols='OpenFlow13')

        h1 = self.addHost('h1', ip='161.24.0.5/24')
        h2 = self.addHost('h2', ip='161.24.0.6/24')
        h3 = self.addHost('h3', ip='161.24.0.7/24')
        h4 = self.addHost('h4', ip='161.24.0.8/24')

        switches = [s1, s2, s3, s4]

        self.addLink(s1, s2, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s1, s3, bw=10, delay='100ms', loss=20,jitter='10ms', use_htb=True)
        self.addLink(s1, s4, bw=10, delay='600ms', loss=20, jitter='10ms', use_htb=True)
        self.addLink(s2, s3, bw=10, delay='200ms', loss=3, jitter='10ms', use_htb=True)
        self.addLink(s2, s4, bw=10, delay='200ms', loss=20, jitter='10ms', use_htb=True)
        self.addLink(s3, s4, bw=10, delay='500ms', loss=3, jitter='10ms', use_htb=True)

        self.addLink(h1, s1, bw=10, delay='0ms', loss=0, use_htb=True)
        self.addLink(h2, s4, bw=10, delay='0ms', loss=0, use_htb=True)
        self.addLink(h3, s3, bw=10, delay='0ms', loss=0, use_htb=True)
        self.addLink(h4, s2, bw=10, delay='0ms', loss=0, use_htb=True)

class ComplexTopo(Topo):

    def __init__(self, delay, jitter, **opts):
        Topo.__init__(self, **opts)

        delay_str = "{}ms".format(delay)
        jitter_str = "{}ms".format(jitter)

        s1 = self.addSwitch('s1', ip='161.24.0.1/24', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', ip='161.24.0.2/24', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', ip='161.24.0.3/24', protocols='OpenFlow13')
        s4 = self.addSwitch('s4', ip='161.24.0.4/24', protocols='OpenFlow13')
        s5 = self.addSwitch('s5', ip='161.24.0.5/24', protocols='OpenFlow13')
        s6 = self.addSwitch('s6', ip='161.24.0.6/24', protocols='OpenFlow13')

        hs = [self.addHost('h%d' % (x+1), ip='161.24.0.%d/24' % (x+7)) for x in xrange(6)]
        ss = [s1, s2, s3, s4, s5, s6]

        self.addLink(s1, s2, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s1, s4, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s2, s3, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s2, s4, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s2, s5, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s3, s5, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s3, s6, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s4, s5, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)
        self.addLink(s5, s6, bw=10, delay=delay_str, loss=3, jitter=jitter_str, use_htb=True)

        for h, s in zip(hs, ss):
            self.addLink(h, s, delay='0ms', loss=0)#!/usr/bin/python

class SimpleTopo(Topo):

    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        s1 = self.addSwitch('s1', ip='161.24.0.1/24', protocols='OpenFlow13')
        s2 = self.addSwitch('s2', ip='161.24.0.2/24', protocols='OpenFlow13')
        s3 = self.addSwitch('s3', ip='161.24.0.3/24', protocols='OpenFlow13')

    	h1 = self.addHost('h1', ip='161.24.0.5/24')
        h2 = self.addHost('h2', ip='161.24.0.6/24')
        h3 = self.addHost('h3', ip='161.24.0.7/24')

        switches = [s1, s2, s3]
        hs = [h1, h2, h3]

        self.addLink(s1, s2, bw=0.5, delay='500ms', loss=1, jitter='100ms', use_htb=True)
        self.addLink(s1, s3, bw=0.5, delay='500ms', loss=1, jitter='0ms', use_htb=True)
        self.addLink(s2, s3, bw=0.5, delay='500ms', loss=1, jitter='0ms', use_htb=True)

        for h, s in zip(hs, switches):
            self.addLink(h, s, bw=0.5, delay='0ms', loss=1, use_htb=True)

def topoTest():
    "Create network and run simple performance test"
    topo = ITATopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    h1, h2, h3 = net.hosts
    net.start()
    #print test_performance(net, h1, h2)
    net.interact()
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topoTest()