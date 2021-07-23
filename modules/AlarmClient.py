#! /usr/bin/python3

import os
import sys
import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../controllers")
from Client import *
from AlarmController import *

socket = Client("alarm", "/tmp/socket")

alarmManager = AlarmManager(socket)

while (1):
    text = socket.recvData()
    tokens = text.split()
    if "status" in tokens:
        socket.sendData("Alarm is green")
    elif "set" in tokens:
        alarmManager.addAlarm(tokens[1:])
    elif "delete" in tokens:
        alarmManager.deleteAlarm(tokens[1:])
    elif "stop" in tokens:
        alarmManager.stopAlarm()
    elif "list" in tokens:
        alarmManager.listAlarms()
    elif "kill" in tokens:
        socket.sendData("SIGKILL")
        socket.close()
        break
