import math

def hops(port_stats, link):
	return 1

def latency(port_stats, link):
	return link[1].latency

def jitter(port_stats, link):
	return link[1].jitter*link[1].jitter

def packet_loss(port_stats, link):
	other_link = port_stats[link[2]][link[3]]
	if float(link[1].cumulative_tx['packets']) == 0:
		return 0
	a = float(other_link[1].cumulative_rx['packets'])/float(link[1].cumulative_tx['packets'])
	if a <= 0:
		return 0
	return -math.log(a)
