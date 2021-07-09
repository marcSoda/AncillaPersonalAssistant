#! /usr/bin/python3
import sys
sys.path.append("../controllers")
from Client import *
from BluetoothController import *

heaterAddr = '98:D3:41:FD:6B:EB'
lightAddr = '00:20:02:20:06:B5'
devices = []
light = Light(["light", "lamp", "desk blanket"], lightAddr)
devices.append(light)

socket = Client("bluetooth", "/tmp/socket")
socket.connect()

while (1):
    text = socket.recvData()
    for device in devices:
        for tag in device.tags:
            if tag in text:
                device.togglePower()
                socket.sendData("Toggled power for " + tag)
                break
