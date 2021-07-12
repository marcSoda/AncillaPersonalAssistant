#! /usr/bin/python3
import sys
sys.path.append("../controllers")
from Client import *
from BluetoothController import *

heaterAddr = '98:D3:41:FD:6B:EB'
lightAddr = '00:20:02:20:06:B5'

deviceManager = DeviceManager()
deviceManager.add(Light(["light", "lamp"], lightAddr))

socket = Client("bluetooth", "/tmp/socket")
socket.connect()

while (1):
    text = socket.recvData()

    if "status" in text:
        status = deviceManager.getDisconnectedDevices()
        if len(status) <= 0: socket.sendData("Bluetooth: green")
        for d in status: socket.sendData(d.tags[0] + " has lost connection")
        continue

    for device in deviceManager.devices:
        for tag in device.tags:
            if tag in text:
                device.togglePower()
                socket.sendData("Toggled power for " + tag)
                break
