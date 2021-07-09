#! /usr/bin/python3
import sys
sys.path.append("../controllers")
from Client import *

import time
c = Client("Test Client", "/tmp/socket")
c.connect()
ctr = 0;
while (1):
    if ctr == 3:
        c.sendData("SIGKILL")
        break
    time.sleep(1)
    c.sendData("Random Data")
    ctr+=1
