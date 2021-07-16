#! /usr/bin/python3

import os
import sys
import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../controllers")
from Client import *

socket = Client("alarm", "/tmp/socket")

days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
alarms = {}

def setAlarm(tokens):
    time = tokens[1:3]
    print(time)
    return "not done"


while (1):
    text = socket.recvData()
    tokens = text.split()
    if "status" in tokens:
        socket.sendData("Alarm: green")
        continue

    if "kill" in tokens:
        socket.sendData("SIGKILL")
        socket.close()
        break

    if "set" in tokens:
        result = setAlarm(tokens)
        socket.sendData(result)
