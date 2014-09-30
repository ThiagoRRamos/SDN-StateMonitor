import re
import time

loss_r = r'(\d+)% packet loss,'

def convert_speed(stringg):
    val = float(stringg.split(" ")[0])
    if stringg.endswith('Mbits/sec'):
        return 1024*val
    if stringg.endswith('Kbits/sec'):
        return val
    raise Error

def test_performance(net, h1, h2):
    lines = h1.cmd('ping -c20 %s' % h2.IP()).splitlines()
    loss_line = lines[-2]
    ploss = float(re.search(loss_r, loss_line).group(1))/100.0
    stats = lines[-1]
    res_stats = re.search(r'([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)', stats)
    pmin, pavg, pmax, pmdev = [float(x) for x in res_stats.groups()]
    going, coming = [convert_speed(x) for x in net.iperf([h1, h2])]
    return pmin, pavg, pmax, pmdev, ploss, going, coming