import re
import time
import itertools

loss_r = r'(\d+)% packet loss,'

def convert_speed(stringg):
    val = float(stringg.split(" ")[0])
    if stringg.endswith('Gbits/sec'):
        return 1024*1024*val
    if stringg.endswith('Mbits/sec'):
        return 1024*val
    if stringg.endswith('Kbits/sec'):
        return val
    raise Error

def test_performance(net, h1, h2, number_pings=20):
    for a, b in itertools.permutations(net.hosts, 2):
        a.cmd('ping -c1 %s' % b.IP())
    time.sleep(3)
    lines = h1.cmd('ping -c{} {}'.format(number_pings, h2.IP())).splitlines()
    if len(lines) < 2:
        raise Error(lines)
    loss_line = lines[-2]
    ploss = float(re.search(loss_r, loss_line).group(1))/100.0
    stats = lines[-1]
    res_stats = re.search(r'([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)', stats)
    if res_stats:
        pmin, pavg, pmax, pmdev = [float(x) for x in res_stats.groups()]
        return pmin, pavg, pmax, pmdev, ploss
    else:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

def start_iperf(client, server):
    server.cmd('killall -9 iperf')
    server.sendCmd("iperf -s -u")
    client.sendCmd("iperf -c -u")