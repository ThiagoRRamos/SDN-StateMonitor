import random
import re
import matplotlib.pyplot as plt
import numpy as np
import random

f = open("../results/loss_results.txt", 'r')

rex = r"(\d+\.?\d*) (\d+\.?\d*) (-?\d+\.?\d*)"

model = []
ping = {}
result = {}

for line in f.readlines():
	lat, pin, res = [float(x) for x in re.findall(rex, line)[0]]
	if lat not in result:
		model.append(lat)
		ping[lat] = []
		result[lat] = []
	result[lat].append(res)
	ping[lat].append(pin) 

print model
model = [100*x for x in sorted(model)]
f_result = [100 * sum(result[x/100])/len(result[x/100]) for x in model]
f_ping = [100 * sum(ping[x/100])/len(ping[x/100]) for x in model]
plt.plot(model, f_result,'g--', label='Controlador')
plt.plot(model, f_ping,'r--', label='Ping')
plt.title("Perda de pacotes")
plt.legend()
plt.grid(True)
plt.ylabel("Perda medida (%)")
plt.xlabel("Perda projetada em cada link (%)")
plt.show()