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
from topologies import SimpleTopo, DenseTopo, ComplexTopo

def testLoss(delay, loss):
    topo = ComplexTopo(delay, 2, loss)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.start()
    h1, h2 = net.hosts[:2]
    time.sleep(10)
    net.iperf([h1,h2])
    pmin, pavg, pmax, pmdev, ploss, jitter = test_pings(h1, h2, 80)
    time.sleep(1)
    l = requests.get("http://localhost:8080/json/link?o=1&d=2").json()
    print ploss, l['round_loss']
    net.stop()

if __name__ == '__main__':
    setLogLevel('error')
    testLoss(int(sys.argv[1]), int(sys.argv[2]))