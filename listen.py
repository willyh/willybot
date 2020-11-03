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
import willybot

numpy.set_printoptions(threshold=numpy.inf)

PLOT = False
CHUNK = 1024
FORMAT = pyaudio.paInt16
SAMPLE_WIDTH = 2 # bytes
CHANNELS = 1
RATE = 44100
FREQ_SECONDS = 2
VOICE_SECONDS = 4
SAMPLE_EVERY = 1
SLEEP_TIME = 0.2
MAX_MATCHING_FREQS = 100

# willy custom values

# Account for noise:
# There must be at least one fourier value greater than this to consider
# the signal to be anything but noise.
background_noise_threshold = 20.0

# Account for noise:
# Any stand-out frequencies lower than this will be ignored.
lowest_human_freq = 0.0016
highest_human_freq = 0.4

# Differ loud noise from tones:
# Number of fourier values that must be greater than the average in order
# to say there frequency that stands out.
greater_than_avg_count = 1000#100

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
    global sock, on_off_thread, program_killed
    print("\nGoodbye! Turning off lamp")
    onoff.turn_off_lamp(sock)
    onoff.app_running = False
    #on_off_thread.join()
    p.terminate()
    program_killed = True
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
    global sound_buffer, buf_mutex
    buf_mutex.acquire()
    for byte in data:
        sound_buffer.append(byte)
    buf_mutex.release()

    return (data, pyaudio.paContinue)

def flush_audio():
    global sound_buffer, buf_mutex
    buf_mutex.acquire()
    sound_buffer.clear()
    buf_mutex.release()


def set_freq_color(sock, process_buf):
    global min_freq, max_freq
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
                                   v[1] > background_noise_threshold,
                                   freq_val_tuples)
        f_vals = list(map(lambda v: v[0], greater))
        print(len(f_vals))
        if len(f_vals) > 0 and len(f_vals) <= MAX_MATCHING_FREQS:
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
                        sock.sendto(lifx.set_color_packet(color), (lifx.IP, lifx.PORT))
                    except:
                        print("Failed to send command to lifx bulb")

                    scope = list(freqs).index(highest_human_freq)
                    avg_list = [metric(avg)] * len(freqs)
                    std = [avg + 3 * numpy.std(fourier_real)] * len(freqs)
                    plot(plt, freqs[0:scope], [fourier_real[0:scope], std[0:scope], avg_list[0:scope]])

def pull_new_bytes(buf_mutex):
    global sound_buffer
    n_bytes = RATE*max(VOICE_SECONDS, FREQ_SECONDS)
    buf_mutex.acquire()
    if len(sound_buffer) < n_bytes:
        buf_mutex.release()
        return bytearray()

    sound_buffer = sound_buffer[-n_bytes:]
    process_buf = bytearray()
    for byte in sound_buffer:
        process_buf.append(byte)
    buf_mutex.release()
    return process_buf

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("0.0.0.0", lifx.PORT))

p = pyaudio.PyAudio()

plt.ion()
plt.show()

sound_buffer = bytearray()
iteration = 0

signal.signal(signal.SIGINT, turn_off_and_exit)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

onoff.turn_on_lamp(sock)
light_on = True
program_killed = False
while not program_killed:
    process_buf = pull_new_bytes(buf_mutex)
    if len(process_buf) == 0:
        time.sleep(SLEEP_TIME)
        continue

    if light_on:
        freq_buf = process_buf[-RATE*FREQ_SECONDS:]
        set_freq_color(sock, freq_buf)

    voice_buf = process_buf[-RATE*VOICE_SECONDS:]
    if willybot.lights_command_given(sock, voice_buf, RATE, SAMPLE_WIDTH):
        if light_on:
            onoff.turn_off_lamp(sock)
        else:
            onoff.turn_on_lamp(sock)
        light_on = not light_on
        flush_audio() # We don't want to process the command twice
