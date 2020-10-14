import numpy
CLAP_LENGTH = 800000 # I eyeballed the length of a clap

initialized = False
energy_l = 0
energy_r = 0
clap_wait = 0
sig_cache = []
# feed in a new chunk of signal and count the number of claps
# this function remembers previous chunks and factors those in
# when looking for new claps
def clap_count(sig):
    global sig_cache, energy_l, energy_r, initialized, clap_wait
    #sig = list(map(lambda x: x if x > 0.1 else 0.0, sig))
    sig_cache += list(sig)
    if not initialized:
        energy_l = numpy.sum(sig_cache[0:CLAP_LENGTH])
        energy_r = numpy.sum(sig_cache[CLAP_LENGTH:2*CLAP_LENGTH])
        sig_cache = sig_cache[CLAP_LENGTH:]
        initialzed = True

    claps = 0
    _last_r = 0
    for i in range(0, len(sig_cache) - CLAP_LENGTH*2):
        energy_l -= sig_cache[i]
        energy_l += sig_cache[i + CLAP_LENGTH]
        energy_r -= sig_cache[i + CLAP_LENGTH]
        energy_r += sig_cache[i + 2 * CLAP_LENGTH]
        if energy_l == 0:
            continue

        if clap_wait > 0:
            clap_wait -= 1
            continue

        ratio = energy_r / energy_l
        if ratio > 6:
            print("clap at " + str(i) + " l: " + str(energy_l) + " r: " + str(energy_r) + " ratio: " + str(ratio))
            claps += 1
            clap_wait = CLAP_LENGTH
    sig_cache = sig_cache[-2*CLAP_LENGTH + 1:]
    return claps

