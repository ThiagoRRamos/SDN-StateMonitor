import math
import sys

def hops(curr_val, port_stats, link):
	return 1

def latency(curr_val, port_stats, link):
	return link[1].latency

def jitter(curr_val, port_stats, link):
	return link[1].jitter*link[1].jitter

def packet_loss(curr_val, port_stats, link):
	other_link = port_stats[link[2]][link[3]]
	sent = float(link[1].cumulative_tx['packets'])
	received = float(other_link[1].cumulative_rx['packets'])
	if sent == 0:
		return 0
	if received == 0:
		return sys.maxint
	a = received / sent
	return -math.log(a)

def sent_packets(curr_val, port_stats, link):
	a = link[1].cumulative_tx['packets']
	if curr_val > a:
		return 0
	return a - curr_val