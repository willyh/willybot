import numpy
CLAP_LENGTH = 7000 # I eyeballed the length of a clap

def clap_count(sig):
    #sig = list(map(lambda x: x if x > 0.1 else 0.0, sig))
    claps = 0
    energy_l = numpy.sum(sig[0:CLAP_LENGTH])
    energy_r = numpy.sum(sig[CLAP_LENGTH:2*CLAP_LENGTH])
    min_valid_index = 0
    for i in range(0, len(sig) - CLAP_LENGTH * 2):
        energy_l -= sig[i]
        energy_l += sig[i + CLAP_LENGTH]
        energy_r -= sig[i + CLAP_LENGTH]
        energy_r += sig[i + 2 * CLAP_LENGTH]
        if energy_l == 0:
            continue

        if i < min_valid_index:
            continue

        ratio = energy_r / energy_l
        if ratio > 5:
            print("clap at " + str(i) + " l: " + str(energy_l) + " r: " + str(energy_r) + " ratio: " + str(ratio))
            claps += 1
            min_valid_index = i + 2 * CLAP_LENGTH
    return claps

