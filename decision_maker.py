def hops(link):
	return 1

def latency(link):
	return link[1].latency

def jitter(link):
	return link[1].jitter*link[1].jitter
