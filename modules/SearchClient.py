#!/usr/bin/python3

import os
import sys
import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../controllers")
from Client import *
from SearchController import *

socket = Client("search", "/tmp/socket")

searchMan = SearchController(socket)

while (1):
    text = socket.recvData()
    tokens = text.split()
    if "status" in tokens:
        socket.sendData("Search is green")
    elif "kill" in tokens:
        socket.sendData("SIGKILL")
        socket.close()
        break
    else:
        try:
            socket.sendData(searchMan.query(text))
        except Exception as e:
            socket.sendData("Search result contains no text data")
