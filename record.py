import numpy
import pyaudio
import wave
import time
import sys
import matplotlib.pyplot as plt

numpy.set_printoptions(threshold=numpy.inf)

N_GARBAGE_CHUNKS = 25
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 2

p = pyaudio.PyAudio()

plt.ion()
plt.show()

combined = bytearray()
chunks = list()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

for i in range(0, int(numpy.ceil(RATE / CHUNK) * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    if i >= N_GARBAGE_CHUNKS:
        chunks.append(data)
        for byte in data:
            combined.append(byte)

stream.stop_stream()
stream.close()

wf = wave.open(sys.argv[1], 'w')
wf.setnchannels(CHANNELS)
wf.setframerate(RATE)
wf.setsampwidth(p.get_sample_size(FORMAT))

for i in range(0, len(chunks)):
    wf.writeframes(chunks[i])

wf.close()

out = p.open(format=FORMAT,
             channels=CHANNELS,
             rate=RATE,
             output=True)

for i in range(0, len(chunks)):
    out.write(chunks[i])

out.stop_stream()
out.close()

plt.cla()
plt.clf()
plt.plot(combined)
plt.draw()
plt.pause(0.001)

time.sleep(2)

p.terminate()
