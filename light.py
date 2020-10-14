import socket
from time import sleep

IP = "255.255.255.255"
PORT = 56700

green = bytes.fromhex('31 00 00 34 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 00 aa aa FF 7F FF FF AC 0D 00 04 00 00')

other = bytes.fromhex('31 00 00 34 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 66 00 00 00 00 11 11 FF FF FF FF AC 0D 00 04 00 00')

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

s.sendto(green, (IP, PORT))
sleep(2)
s.sendto(other, (IP, PORT))
