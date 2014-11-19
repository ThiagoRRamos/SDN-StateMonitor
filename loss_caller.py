from subprocess import Popen
import time
import os

fil = open("results/loss_results.txt", 'a')
control_logger = open("results/logger.txt", 'w')
null = open(os.devnull, 'w')

cleaner = Popen(['sudo', 'mn','--clean'], stdout=null, stderr=null)
cleaner.wait()
count = 0
for i in xrange(5):
	for de in xrange(2):
		for ji in xrange(9):
			count += 1
			delay = 25 * (de + 1)
			loss = 2 * ji
			print "{} - Starting in {} - {}".format(count, delay, loss)
			controller = Popen(['/home/ubuntu/ryu/bin/ryu-manager','/home/ubuntu/SDN-StateMonitor/state_monitor.py'], stdout=control_logger)
			mininet = Popen(['sudo', 'python','topos/loss_test.py', str(delay), str(loss)], stdout=fil)
			mininet.wait()
			controller.kill()
			print "Finished in {} - {}".format(delay, loss)
			time.sleep(5)