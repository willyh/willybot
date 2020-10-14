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
import onoff

import lightutil

numpy.set_printoptions(threshold=numpy.inf)

PLOT = False
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
background_noise_threshold = 20.0

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

def turn_off_and_exit(sig_num, stack_frame):
    global s, on_off_thread
    print("\nGoodbye! Turning off lamp")
    onoff.turn_off_lamp(s)
    onoff.app_running = False
    #on_off_thread.join()
    p.terminate()
    exit(0)

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

def listen(s):
    global combined, min_freq, max_freq
    time.sleep(SLEEP_TIME)

    n_bytes = RATE*RECORD_SECONDS
    if len(combined) < n_bytes:
        return

    buf_mutex.acquire()
    new_bytes = bytearray()
    for byte in combined[n_bytes:]:
        new_bytes.append(byte)

    combined = combined[-n_bytes:]
    process_buf = bytearray()
    for byte in combined:
        process_buf.append(byte)
    buf_mutex.release()

    sig = numpy.frombuffer(process_buf, dtype='<i2').reshape(-1, CHANNELS)
    sig = sig[0:,0]

    # find frequency
    sig = sig / (2 ** 15)

    fourier = numpy.fft.fft(sig)
    freqs = numpy.fft.fftfreq(sig.size)
    num_positive = int(sig.size/2)

    # only consider positive frequencies
    fourier = fourier[0:num_positive]
    freqs = freqs[0:num_positive]
    fourier_real = list(numpy.sqrt(fourier.real**2+fourier.imag**2))

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
            freq = f_vals[0]

            if freq > 0:
                if min_freq == None or freq < min_freq:
                    min_freq = freq
                if max_freq == None or freq > max_freq:
                    max_freq = freq
                if min_freq < max_freq:
                    color = freq_to_color(freq)
                    print("set color " + str(color))
                    try:
                        s.sendto(lifx.set_color_packet(color), (lifx.IP, lifx.PORT))
                    except:
                        print("Failed to send command to lifx bulb")
                        return

                scope = list(freqs).index(highest_human_freq)
                avg_list = [metric(avg)] * len(freqs)
                avg2 = [avg] * len(freqs)
                avg3 = [avg ** 2 + 200] * len(freqs)
                avg4 = [avg ** 3 + 200] * len(freqs)
                std = [avg + 3 * numpy.std(fourier_real)] * len(freqs)
                plot(plt, freqs[0:scope], [fourier_real[0:scope], std[0:scope], avg_list[0:scope]])

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(("0.0.0.0", lifx.PORT))

p = pyaudio.PyAudio()

plt.ion()
plt.show()

combined = bytearray()
iteration = 0

signal.signal(signal.SIGINT, turn_off_and_exit)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

def listen_target(s, cv):
    while True:
        cv.acquire()
        while not onoff.willy_present:
            cv.wait()
        listen(s)
        cv.release()

cv = threading.Condition()
on_off_thread = threading.Thread(target=onoff.contact_willy, args=(s,cv,))
listen_thread = threading.Thread(target=listen_target, args=(s, cv,))
on_off_thread.start()
listen_thread.start()
