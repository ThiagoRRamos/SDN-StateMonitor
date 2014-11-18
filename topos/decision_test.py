import sys
import time

from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel

import requests

from topo_utils import test_pings
from topo_utils import MyLogger
from topologies import SimpleTopo, DenseTopo, DifferentTopo

def testDecision(delay, jitter):
    topo = DifferentTopo(delay, jitter)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.start()
    h1, h2, h3, h4, h5 , h6 = net.hosts
    time.sleep(10)
    pmin, pavg, pmax, pmdev, ploss, jitter = test_pings(h1, h6, 40)
    print delay, jitter, pavg
    net.stop()

if __name__ == '__main__':
    setLogLevel('error')
    testDecision(int(sys.argv[1]), int(sys.argv[2]))