import time
import lifx

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
        time.sleep(0.5)

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
            print("trying to turn off lamp")
            set_lamp(s, False)
            lamp_on = False
        except:
            print("Failed to send command to lifx bulb")
            time.sleep(1)
    return set_lamp(s, False)
