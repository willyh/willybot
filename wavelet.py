import numpy
import pyaudio
import pywt
import wave
import time
import matplotlib.pyplot as plt

numpy.set_printoptions(threshold=numpy.inf)

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 1024 #44100
RECORD_SECONDS = 1
SAMPLE_EVERY = 1

p = pyaudio.PyAudio()

plt.ion()
plt.show()

combined = bytearray()
iteration = 0

while 1:
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    for i in range(0, int(numpy.ceil(RATE / CHUNK) * SAMPLE_EVERY)):
        data = stream.read(CHUNK)
        for byte in data:
            combined.append(byte)

    stream.stop_stream()
    stream.close()

    iteration += 1

    if iteration <= 2: # first sampling is garbage
        continue

    n_bytes = RATE*RECORD_SECONDS
    if len(combined) < n_bytes:
        continue
    else:
        combined = combined[len(combined)-n_bytes:len(combined)]

    sig = numpy.frombuffer(combined, dtype='<i2').reshape(-1, CHANNELS)
    sig = sig[0:n_bytes,0]
    sig = sig / (2 ** 15)

    fourier = numpy.fft.fft(sig)
    freqs = numpy.fft.fftfreq(sig.size)

    transform = list(map(lambda x: x if x > 50 else 0, list(fourier.real)))
    low_pass_filter = list(map(lambda x: x if numpy.abs(x) > 0.6 else 0, sig))
    MAX_CLAP_FREQ = 0.6
    freq_val = list(map(lambda v: v[1] if numpy.abs(freqs[v[0]]) < 0.76 else 0, enumerate(fourier.real)))
    avg_num = 1 # 1 / clap freq = .01
    sig_sum = 0.0
    avg = list()
    for i in range(0, len(sig) - avg_num):
        sig_sum += sig[i]
        if i >= avg_num:
            avg.append(sig_sum / avg_num)
            sig_sum -= sig[i - avg_num]

    plt.cla()
    plt.clf()
    sigApprx, sigDetail = pywt.dwt(sig, 'haar')
    plt.plot(sigDetail)
    #plt.plot(avg)
    #plt.plot(freqs, freq_val)
    plt.draw()
    plt.pause(0.001)

p.terminate()
