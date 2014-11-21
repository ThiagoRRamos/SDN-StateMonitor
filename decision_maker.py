import math
import sys

# Yeah, I have to set the speeds manually. It should not be needed on a real world. But OVS doesn't allow that.
# See http://openvswitch.org/pipermail/discuss/2014-October/015304.html

speeds = {
	1: {2: 10, 4: 1},
	2: {1: 10, 3: 10, 4: 1, 5: 100},
	3: {2: 10,5: 1, 6: 1},
	4: {1: 1, 2: 1, 5: 10},
	5: {2: 100, 3: 1, 4: 10, 6: 10},
	6: {3: 1, 5: 10},
}

def hops(curr_val, port_stats, link):
	return 1

def latency(curr_val, port_stats, link):
	return link[1].latency

def jitter(curr_val, port_stats, link):
	return link[1].jitter

def available_speed(curr_val, port_stats, link):
	this_dp = int(link[0].name[1])
	dst_dp = link[2]
	speed = 1024 * 1024 * speeds[this_dp][dst_dp]
	used_speed = link[1].speed_tx['bytes']
	print this_dp, dst_dp, speed, used_speed
	if curr_val > sys.maxint - speed + used_speed:
		return 0
	return sys.maxint - speed + used_speed - curr_val

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