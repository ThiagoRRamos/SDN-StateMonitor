from subprocess import Popen
import time
import os

fil = open("results/latency_results.txt", 'a')
control_logger = open("results/logger.txt", 'w')
null = open(os.devnull, 'w')

RANGE_DE = 10

cleaner = Popen(['sudo', 'mn','--clean'], stdout=null, stderr=null)
cleaner.wait()
for i in xrange(5):
	for de in xrange(RANGE_DE):
		for ji in xrange(5):
			delay = 25 * (RANGE_DE - de)
			jitter = 5 * (ji + 1)
			print "Starting in {} - {}".format(delay, jitter)
			controller = Popen(['/home/ubuntu/ryu/bin/ryu-manager','/home/ubuntu/SDN-StateMonitor/state_monitor.py'], stdout=control_logger)
			mininet = Popen(['sudo', 'python','topos/latency_test.py', str(delay), str(jitter)], stdout=fil)
			mininet.wait()
			controller.kill()
			print "Finished in {} - {}".format(delay, jitter)