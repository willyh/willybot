IP = "255.255.255.255"
PORT = 56700

set_color_hdr = bytes.fromhex('31 00 00 34 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00')
set_color_rsvd = bytes.fromhex('00')
saturation = bytes.fromhex('FF FF')
brightness = bytes.fromhex('FF 7F')
kelvin = bytes.fromhex('AC 0D')
duration = bytes.fromhex('00 04 00 00')

set_power_hdr = bytes.fromhex('26 00 00 34 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 15 00 00 00')
power_on = bytes.fromhex('ff ff')
power_off = bytes.fromhex('00 00')

get_power_hdr = bytes.fromhex('24 00 00 34 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 14 00 00 00')

is_on = False

def get_power_packet():
    return b''.join([get_power_hdr])

def get_power_from_state_packet(p):
    #print(p)
    p_len = p[0]
    power = int.from_bytes(p[36:38], "big")
    #print(power)
    return power > 0

def set_power_packet(on):
    power = power_on if on else power_off
    return b''.join([set_power_hdr, power])

def set_color_packet(color):
    p = [
            set_color_hdr,
            set_color_rsvd,
            color,
            saturation,
            brightness,
            kelvin,
            duration,
        ]
    return b''.join(p)
