from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from mininet.link import TCLink, TCIntf
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

from topo_utils import test_performance
from topologies import SimpleTopo, DenseTopo, ComplexTopo

def runAndInteractTopology():
    "Create network and run simple performance test"
    topo = ComplexTopo(100, 10)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=RemoteController)
    net.start()
    net.interact()
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    runAndInteractTopology()