import sys

from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel

import requests

from topo_utils import test_pings
from topo_utils import MyLogger
from topologies import SimpleTopo, DenseTopo, ComplexTopo

def testLatency(delay, jitter):
    if jitter < delay:
        topo = ComplexTopo(delay, jitter)
        net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
        net.start()
        h1, h2 = net.hosts[:2]
        res = str(test_pings(net, h1, h2))
        l = requests.get("http://localhost:8080/json/latencies").json()
        j = requests.get("http://localhost:8080/json/jitters").json()
        meas = l['1']['2'] + l['2']['1']
        print "{} {} - {} - {} {} {}".format(delay, jitter, res, meas, j['1']['2'], j['2']['1'])
        net.stop()

if __name__ == '__main__':
    setLogLevel('error')
    testLatency(int(sys.argv[1]), int(sys.argv[2]))