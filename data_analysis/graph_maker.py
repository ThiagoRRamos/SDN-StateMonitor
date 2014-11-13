#!/usr/bin/python
# -*- coding: latin-1 -*-

import random
import re
import matplotlib.pyplot as plt
import numpy as np

ree = r"(\d+) (\d+) - \((.*),(.*),(.*),(.*),(.*),(.*)\) - (\d\.\d+) (\d\.\d+) (\d\.\d+)" 

f = open("../results/latency_results.txt", 'r')

l_results_l = {}
l_results_p = {}
j_results_l = {}
j_results_p = {}

for line in f.readlines():
	d, j, mi, me, ma, dp, lo, jit, lam, jitm1, jitm2 = [float(x) for x in re.findall(ree, line)[0]]
	if d not in l_results_l:
		l_results_l[d] = []
		l_results_p[d] = []
	if j not in j_results_l:
		j_results_l[j] = []
		j_results_p[j] = []
	j_results_l[j] += [jitm1 + jitm2]
	j_results_p[j] += [jit]
	l_results_l[d] += [lam]
	l_results_p[d] += [me]

latency_model = [50.0*(x+1) for x in xrange(10)]
my_latency = [1000 * sum(l_results_l[x/2]) / 25 for x in latency_model]
my_latency_error = [1000 * np.std(l_results_l[x/2]) for x in latency_model]
ping_latency = [sum(l_results_p[x/2]) / 25 for x in latency_model]
ping_latency_error = [np.std(l_results_p[x/2]) for x in latency_model]

jitter_model = [2*5.0*(x+1) for x in xrange(5)]
my_jitter = [1000 * sum(j_results_l[x/2]) /25 for x in jitter_model]
my_jitter_error = [1000 * np.std(j_results_l[x/2]) for x in jitter_model]
ping_jitter = [sum(j_results_p[x/2]) /25 for x in jitter_model]
ping_jitter_error = [np.std(j_results_p[x/2]) for x in jitter_model]

def make_graph(model, my_results, ping_results, title, xlabel, ylabel):
	plt.plot(model, my_results,'g--', label='Controlador')
	plt.plot(model, ping_results, 'r--', label='Ping')
	plt.title(title)
	plt.legend()
	plt.grid(True)
	plt.ylabel(ylabel)
	plt.xlabel(xlabel)

def make_graph_with_error_bars(model, my_results, ping_results, my_error, ping_error, title, xlabel, ylabel):
	plt.errorbar(model, my_results, my_error, 0.0, 'g--', label='Controlador')
	plt.errorbar(model, ping_results, ping_error, 0.0, 'r--', label='Ping')
	plt.title(title)
	plt.legend()
	plt.grid(True)
	plt.ylabel(ylabel)
	plt.xlabel(xlabel)

def make_latency_graph(model, my_results, ping_results, my_error, ping_error):
	return make_graph_with_error_bars(model, my_results, ping_results, my_error, ping_error,
		u"Medidor de Latencia", u'Latencia idealmente projetada (ms)', u'Latencia medida (ms)')

def make_jitter_graph(model, my_results, ping_results, my_error, ping_error):
	return make_graph_with_error_bars(
		model, my_results, ping_results, my_error, ping_error ,u"Medidor de Jitter",
		u'Jitter idealmente projetado (ms)', u'Jitter medido (ms)')

make_latency_graph(latency_model, my_latency, ping_latency, my_latency_error, ping_latency_error)
plt.show()
make_jitter_graph(jitter_model, my_jitter, ping_jitter, my_jitter_error, ping_jitter_error)
plt.show()

