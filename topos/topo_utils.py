import re
import time
import itertools

loss_r = r'(\d+)% packet loss,'

class MyLogger(object):

    def __init__(self, path):
        self.path = path
        self.file = open(path, 'w')

    def write(self, message, *args):
        message = str(message)
        m = message.format(*args)
        self.file.write(m)
        self.file.write("\n")
        print "Writing:", m


def convert_speed(stringg):
    val = float(stringg.split(" ")[0])
    if stringg.endswith('Gbits/sec'):
        return 1024*1024*val
    if stringg.endswith('Mbits/sec'):
        return 1024*val
    if stringg.endswith('Kbits/sec'):
        return val
    raise Exception

latencies_r = r"time=(\d+\.?\d*) ms"

def measure_jitter(latencies):
    jitter = 0.0
    for prev, l in zip(latencies,latencies[1:]):
        jitter = jitter + (abs(l - prev) - jitter)/16.0
    return jitter

def test_pings(net, h1, h2, number_pings=40):
    time.sleep(80)
    lines = h1.cmd('ping -c{} {}'.format(number_pings, h2.IP())).splitlines()
    if len(lines) < 2:
        raise Exception(lines)
    results = [float(re.search(latencies_r, line).group(1)) for line in lines if re.search(latencies_r, line)]
    jitter = measure_jitter(results)
    loss_line = lines[-2]
    ploss = float(re.search(loss_r, loss_line).group(1))/100.0
    stats = lines[-1]
    res_stats = re.search(r'([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)', stats)
    time.sleep(2)
    if res_stats:
        pmin, pavg, pmax, pmdev = [float(x) for x in res_stats.groups()]
        return pmin, pavg, pmax, pmdev, ploss, jitter
    else:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

def start_iperf(client, server):
    server.cmd('killall -9 iperf')
    server.sendCmd("iperf -s -u")
    client.sendCmd("iperf -c -u")