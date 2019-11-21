import threading
import socket
import select
import pyaudio
import wave
import signal
import time
import numpy
import lifx
import matplotlib.pyplot as plt

import lightutil

numpy.set_printoptions(threshold=numpy.inf)

PLOT = True
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 2
SAMPLE_EVERY = 1
SLEEP_TIME = 0.2

# willy custom values

# Account for noise:
# There must be at least one fourier value greater than this to consider
# the signal to be anything but noise.
background_noise_threshold = 1000.0

# Account for noise:
# Any stand-out frequencies lower than this will be ignored.
lowest_human_freq = 0.0016
highest_human_freq = 0.05

# Differ loud noise from tones:
# Number of fourier values that must be greater than the average in order
# to say there frequency that stands out.
greater_than_avg_count = 10000#100

min_freq = None
max_freq = None

IP = "255.255.255.255"
PORT = 56700

lamp_state_unknown = True
lamp_on = False

buf_mutex = threading.Lock()

def metric(avg):
    return (avg ** 2) + background_noise_threshold

def freq_to_color(f):
    max_color = (2 ** 16) - 1
    x = (numpy.log2(f) % 1.0) * max_color
    #x = (float(f) - min_freq) / (max_freq - min_freq) * max_color
    i = int(x)
    #print(str(i) + ", " + str(i >> 8))
    b = bytes([(i & 0xff), ((i >> 8) & 0xff)])
    #print("color: " + str(b) + " freq: " + str(f) + " val: " + str(i))
    return b

# on - state = True, off - state = False
def set_lamp(state):
    global s
    global lamp_on
    global lamp_state_unknown
    if state:
        print("Lights on")
    else:
        print("Lights off")

    if lamp_state_unknown:
        s.sendto(lifx.set_power_packet(state), (IP, PORT))
        p = s.recv(48)
        lamp_on = lifx.get_power_from_state_packet(p)
        lamp_state_unknown = False

    while lamp_on != state:
        s.sendto(lifx.set_power_packet(state), (IP, PORT))
        p = s.recv(48)
        s.sendto(lifx.get_power_packet(), (IP, PORT))
        p = s.recv(48)
        lamp_on = lifx.get_power_from_state_packet(p)

def turn_on_lamp():
    return set_lamp(True)

def turn_off_lamp():
    return set_lamp(False)

def turn_off_and_exit(sig_num, stack_frame):
    print("\nGoodbye! Turning off lamp")
    turn_off_lamp()
    exit(0)

def resonance_transform(freqs, fourier):
    max_val = float(max(fourier))
    n = len(fourier)
    seen = list()
    resonance = [0] * n
    for i in range(1, n):
        k = n - i
        resonance[k] = float(fourier[k]) / max_val
        seen_del = list()
        for j in seen:
            if freqs[k] < freqs[j] and (freqs[j] % freqs[k]) == 0:
                resonance[k] *= resonance[j]
                seen_del.append(j)
        for j in seen_del:
            seen.remove(j)
        seen.append(k)
    return list(map(lambda x: max_val * x, resonance))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(("0.0.0.0", PORT))
turn_on_lamp()

p = pyaudio.PyAudio()

plt.ion()
plt.show()

combined = bytearray()
iteration = 0

signal.signal(signal.SIGINT, turn_off_and_exit)

def plot(plt, x, y_list):
    if PLOT:
        plt.cla()
        plt.clf()
        for y in y_list:
            plt.plot(x, y)
        plt.draw()
        plt.pause(0.001)

def callback(data, frame_count, time_info, status_flags):
    global combined
    buf_mutex.acquire()
    for byte in data:
        combined.append(byte)
    buf_mutex.release()

    return (data, pyaudio.paContinue)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

while 1:
    time.sleep(SLEEP_TIME)

    listen_bytes = int(numpy.ceil(RATE / CHUNK) * SAMPLE_EVERY)
    n_bytes = RATE*RECORD_SECONDS
    if len(combined) < n_bytes:
        continue

    buf_mutex.acquire()
    combined = combined[len(combined) - n_bytes:len(combined)]
    process_buf = combined
    buf_mutex.release()
    """
    for i in range(0, listen_bytes):
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

"""
    sig = numpy.frombuffer(process_buf, dtype='<i2').reshape(-1, CHANNELS)
    sig = sig[0:n_bytes,0]

    # find frequency
    sig = sig / (2 ** 15)

    if lightutil.clap_count(numpy.abs(sig)) > 1:
        set_lamp(not lamp_on)
        plot(plt, numpy.arange(len(sig)), [sig])
        continue

    fourier = numpy.fft.fft(sig)
    freqs = numpy.fft.fftfreq(sig.size)
    num_positive = int(sig.size/2)

    # only consider positive frequencies
    fourier = fourier[0:num_positive]
    freqs = freqs[0:num_positive]
    fourier_real = list(numpy.absolute(fourier.real))

    avg = numpy.average(fourier_real)
    max_f_val = numpy.max(fourier_real)
    not_background_noise = max_f_val > background_noise_threshold
    if not_background_noise:
        freq_val_tuples = map(lambda v: (freqs[v[0]], v[1]), enumerate(fourier_real))
        greater = filter(lambda v: v[0] > lowest_human_freq and
                                   v[0] < highest_human_freq and
                                   v[1] > metric(avg), freq_val_tuples)
        f_vals = list(map(lambda v: v[0], greater))
        if len(f_vals) > 0:
            """
            print("max: " + str(max_f_val) +
                  " average: " + str(avg) +
                  " num>avg: " + str(len(list(filter(lambda v: v > avg, fourier_real)))))
            print("freq range: " + str(min_freq) + "-" + str(max_freq))
            print("f_vals: " + str(f_vals))
            """
            freq = f_vals[0]

            if freq > 0:
                if min_freq == None or freq < min_freq:
                    min_freq = freq
                if max_freq == None or freq > max_freq:
                    max_freq = freq
                if min_freq < max_freq:
                    color = freq_to_color(freq)
                    s.sendto(lifx.set_color_packet(color), (IP, PORT))

                scope = list(freqs).index(highest_human_freq)
                #resonance = resonance_transform(freqs[0:scope], fourier_real[0:scope])
                avg_list = [metric(avg)] * len(freqs)
                avg2 = [avg] * len(freqs)
                avg3 = [avg ** 2 + 200] * len(freqs)
                avg4 = [avg ** 3 + 200] * len(freqs)
                std = [avg + 3 * numpy.std(fourier_real)] * len(freqs)
                plot(plt, freqs[0:scope], [fourier_real[0:scope], std[0:scope], avg_list[0:scope]])
                #plt.plot(freqs[0:scope], resonance)
                #plt.plot(freqs[0:scope], avg2[0:scope])
                #plt.plot(freqs[0:scope], avg3[0:scope])
                #plt.plot(freqs[0:scope], avg4[0:scope])

p.terminate()
