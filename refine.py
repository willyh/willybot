import numpy
import pyaudio
import pywt
import wave
import time
import sys
import matplotlib.pyplot as plt

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 2

wf = wave.open(sys.argv[1], 'r')

p = pyaudio.PyAudio()

plt.ion()
plt.show()

combined = bytearray()

data = wf.readframes(CHUNK)
while len(data) > 0:
    for byte in data:
        combined.append(byte)
    data = wf.readframes(CHUNK)

sig = numpy.frombuffer(combined, dtype='<i2')#.reshape(-1, CHANNELS)
m = max(sig)
print(m)
#sig = list(map(lambda x: x if numpy.abs(x) > 2000 else 0, sig))

# shorten manually here
sig = sig[9500:23000]
print(sig)

plt.cla()
plt.clf()
plt.plot(sig)
plt.draw()
plt.pause(0.001)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=wf.getframerate(),
                output=True)

chunks = list()
for i in range(0, int(numpy.ceil(len(combined) / CHUNK))):
    chunk = sig[i*CHUNK:(i+1)*CHUNK]
    stream.write(numpy.asarray(chunk).tobytes())
    chunks.append(chunk)

stream.close()

if len(sys.argv) > 2:
    wf = wave.open(sys.argv[2], 'w')
    wf.setnchannels(CHANNELS)
    wf.setframerate(RATE)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    for i in range(0, len(chunks)):
        wf.writeframes(chunks[i])
    wf.close()

while True:
    time.sleep(10)
