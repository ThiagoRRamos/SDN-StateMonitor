#!/usr/bin/python
# -*- coding: latin-1 -*-

import random
import re
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

ree = r"(\d+) (\d+) - \((.*),(.*),(.*),(.*),(.*)\) - (\d\.\d+)"

f = open("../results/aa.txt", 'r')

results_l = {}
results_p = {}

for line in f.readlines():
	d, j, mi, me, ma, dp, lo, lam = [float(x) for x in re.findall(ree, line)[0]]
	if d not in results_l:
		results_l[d] = 0.0
		results_p[d] = 0.0
	results_l[d] += lam/5
	results_p[d] += me/5

model = [50.0*(x+1) for x in xrange(10)]
my_r = [1000 * results_l[x/2] for x in model]
ping_r = [results_p[x/2] for x in model]

def make_latency_graph(model, my_results, ping_results):
	plt.plot(model, my_results,'g--', label='Controlador')
	plt.plot(model, ping_results, 'r--', label='Ping')
	plt.title(u"Medidor de Latencia")
	plt.legend()
	plt.grid(True)
	plt.ylabel(u'Latencia medida (ms)')
	plt.xlabel(u'Latencia idealmente projetada (ms)')


make_latency_graph(model, my_r, ping_r)
plt.show()

