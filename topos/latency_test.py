from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel

from topo_utils import test_pings
from topo_utils import MyLogger
from topologies import SimpleTopo, DenseTopo, ComplexTopo

def runAndTestLatency():
    "Create network and run simple performance test"
    log = MyLogger("../results/latency.txt")
    for delay_i in xrange(10):
        for jitter_i in xrange(5):
            delay = 25 * delay_i
            jitter = 10 * jitter_i
            if jitter < delay:
                topo = ComplexTopo(delay, jitter)
                net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
                net.start()
                h1, h2 = net.hosts[:2]
                log.write("{} {} - {}", delay, jitter, str(test_pings(net, h1, h2)))
                net.stop()

def testLatency(delay, jitter):
    if jitter < delay:
        topo = ComplexTopo(delay, jitter)
        net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
        net.start()
        h1, h2 = net.hosts[:2]
        print "{} {} - {}".format(delay, jitter, str(test_pings(net, h1, h2)))
        net.stop()

if __name__ == '__main__':
    setLogLevel('error')
    runAndTestLatency()