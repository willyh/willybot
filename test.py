import numpy
import pyaudio
import pywt
import wave
import time
import sys
import matplotlib.pyplot as plt
import lightutil

numpy.set_printoptions(threshold=numpy.inf)

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 2

wf = wave.open(sys.argv[1], 'r')

combined = bytearray()

data = wf.readframes(CHUNK)
while len(data) > 0:
    for byte in data:
        combined.append(byte)
    data = wf.readframes(CHUNK)

wf.close()

plt.ion()
plt.show()
plt.cla()
plt.clf()
sample = numpy.frombuffer(combined, dtype='<i2')#.reshape(-1, CHANNELS)
sigApprx = numpy.abs(sample / (2 ** 15))
#sigApprx = list(map(lambda x: x if x > 0.5 else 0.0, sigApprx))
coeffs = list()
print(lightutil.clap_count(sigApprx))
plt.plot(sigApprx)
plt.draw()
plt.pause(0.001)

"""
for i in range(0, 5):
sigApprx, sigDetail = pywt.dwt(sigApprx, 'db1')
coeffs.append(sigDetail)
# read 2nd wave
if len(sys.argv) > 2:
wf = wave.open(sys.argv[2], 'r')
combined = bytearray()
data = wf.readframes(CHUNK)
while len(data) > 0:
    for byte in data:
        combined.append(byte)
    data = wf.readframes(CHUNK)
wf.close()

sample = numpy.frombuffer(combined, dtype='<i2')
sigApprx = sample
coeffs = list()
for i in range(0, 9):
    sigApprx, sigDetail = pywt.dwt(sigApprx, 'db1')
    coeffs.append(sigDetail)
plt.plot(sigApprx)
plt.draw()
plt.pause(10.001)
"""
"""
metrics = list()
sig = numpy.frombuffer(combined, dtype='<i2')
for i in range(0, len(combined) - len(sample)):
match = sig[i:i + len(sample)]
compare_coef = list()
for z in range(0, 4):
    match, tmp = pywt.dwt(match, 'db')
    compare_coef.append(tmp)

metric = 0.0
count = 0
for j in range(0, len(compare_coef)):
    for k in range(0, len(compare_coef[j])):
        metric += numpy.abs(compare_coef[j][k] - coeffs[j][k])
        count += 1
if count > 0:
    metric = metric / count
metrics.append(metric)

plt.ion()
plt.show()
plt.cla()
plt.clf()
plt.plot(metrics)
plt.draw()
plt.pause(0.001)
"""

while True:
    time.sleep(5)
    plt.draw()
    plt.pause(10.001)
