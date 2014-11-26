from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel
import itertools
from topologies import SpecialTopo
from mininet.cli import CLI

from topo_utils import test_pings
import requests

import time

def runAndInteractTopology():
    "Create network and run simple performance test"
    topo = SpecialTopo(100, 10)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.start()
    net.interact()
    net.stop()

def testDecisionTopology():
    "Create network and run simple performance test"
    topo = SpecialTopo(100, 10)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.start()
    time.sleep(10)
    h1, h2, h3, h4, h5, h6 = net.hosts
    pairs = [(h1, h2), (h2, h3), (h4, h5), (h5, h6), (h1, h4), (h2, h5), (h3, h6), (h2, h4), (h3, h5)]
    for a,b in pairs:
        net.ping([a,b])
        net.iperf([a,b])
    for i in xrange(4):
        j = requests.get("http://localhost:8080/set?f={}".format(i)).json()
        print j["message"]
        print test_pings(h1, h6, 40)
        print net.iperf([h1,h6], l4Type='UDP', udpBw='10M')
        time.sleep(20)
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    testDecisionTopology()