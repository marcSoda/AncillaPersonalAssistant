#! /usr/bin/python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../controllers")
from Client import *
from BluetoothController import *

heaterAddr = '98:D3:41:FD:6B:EB'
lightAddr = '00:20:02:20:06:B5'

deviceManager = DeviceManager()
deviceManager.add(Light(["light", "lamp"], lightAddr))

socket = Client("bluetooth", "/tmp/socket")

while (1):
    text = socket.recvData()
    if "status" in text:
        status = deviceManager.getDisconnectedDevices()
        if len(status) <= 0: socket.sendData("Bluetooth: green")
        for d in status: socket.sendData(d.tags[0] + " has lost connection")
        continue

    if "kill" in text:
        socket.sendData("SIGKILL")
        socket.close()
        sys.exit(0)

    for device in deviceManager.devices:
        for tag in device.tags:
            if tag in text:
                response = device.process(text)
                socket.sendData(response)
                break
