#from scapy.all import IP, ICMP, sr1
import time
import threading
import lifx
import subprocess
import signal

WILLY_IP = "192.168.1.15"
TIMEOUT = 1
willy_present = False
app_running = True
def contact_willy(s, cv):
    global willy_present, app_running
    while app_running:
        #if sr1(IP(dst=WILLY_IP)/ICMP(), timeout=TIMEOUT, verbose=0):
        if subprocess.run(["ping", WILLY_IP, "-q", "-c 1", "-w %d" % (TIMEOUT)]).returncode == 0:
            cv.acquire()
            if not willy_present:
                willy_present = True
                turn_on_lamp(s)
                cv.notify()
            cv.release()
        else:
            cv.acquire()
            if willy_present:
                willy_present = False
                turn_off_lamp(s)
            cv.release()
        time.sleep(5)

lamp_state_unknown = True
lamp_on = False

# on - state = True, off - state = False
def set_lamp(s, state):
    global lamp_on
    global lamp_state_unknown
    if state:
        print("Lights on")
    else:
        print("Lights off")

    if lamp_state_unknown:
        s.sendto(lifx.set_power_packet(state), (lifx.IP, lifx.PORT))
        p = s.recv(48)
        lamp_on = lifx.get_power_from_state_packet(p)
        lamp_state_unknown = False

    while lamp_on != state:
        s.sendto(lifx.set_power_packet(state), (lifx.IP, lifx.PORT))
        p = s.recv(48)
        s.sendto(lifx.get_power_packet(), (lifx.IP, lifx.PORT))
        p = s.recv(48)
        lamp_on = lifx.get_power_from_state_packet(p)

def turn_on_lamp(s):
    lamp_on = False
    while not lamp_on:
        try:
            set_lamp(s, True)
            lamp_on = True
        except:
            print("Failed to send command to lifx bulb")
            time.sleep(1)

def turn_off_lamp(s):
    lamp_on = True
    while lamp_on:
        try:
            set_lamp(s, False)
            lamp_on = False
        except:
            print("Failed to send command to lifx bulb")
            time.sleep(1)
    return set_lamp(s, False)
