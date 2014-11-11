from subprocess import Popen
import time

fil = open("results/latency_results.txt", 'w')
control_logger = open("results/logger.txt", 'w')

cleaner = Popen(['sudo', 'mn','--clean'])
cleaner.wait()
for i in xrange(1):
	for de in xrange(10):
		for ji in xrange(5):
			delay = 25 * (10 - de)
			jitter = 5 * ji
			print "Starting in {} - {}".format(delay, jitter)
			controller = Popen(['/home/ubuntu/ryu/bin/ryu-manager','/home/ubuntu/SDN-StateMonitor/state_monitor.py'], stdout=control_logger)
			mininet = Popen(['sudo', 'python','topos/latency_test.py', str(delay), str(jitter)], stdout=fil,stderr=fil)
			while mininet.poll() is None:
				time.sleep(2)
			controller.kill()
			print "Finished in {} - {}".format(delay, jitter)