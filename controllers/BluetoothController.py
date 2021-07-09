#! /usr/bin/python3

import socket

class Device:
    tags = []
    macAddress = ''
    port = 0
    socket = None
    connected = False
    def __init__(self, tags, macAddress, port):
        self.tags = tags
        self.macAddress = macAddress
        self.port = port
        self.connect()

    def send(self, msg):
        try: self.socket.sendall(bytes(msg, 'utf-8'))
        except: self.checkConnection()

    def checkConnection(self):
        try: self.socket.send(bytes("bump data", 'utf-8'))
        except Exception as e:
            print(e, "in Device.checkConnection(self)") #SLOPPY FIX ENTIRE EXCEPT
            self.connected = False
        return self.connected

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.socket.connect((self.macAddress, self.port))
        except:
            print("FAILED TO CONNECT in Device.connect(self)")
            return False
        self.connected = True
        return True

    def reconnect(self):
        print("attempting to reconnect ", self.tags[0])
        self.destroy()
        self.connect()

    def destroy(self):
        if self.connected:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.connected = False

class Light(Device):
    def __init__(self, tags, macAddress, port=1):
        super().__init__(tags, macAddress, port)

    def powerOn(self):
        self.send('1')

    def powerOff(self):
        self.send('0')

    def togglePower(self):
        self.send('2')

    #for bt thread
    # def ensureConnection():
    #     while devices:
    #         unconnectedDevices = []
    #         for device in devices:
    #         if not device.checkConnection(): unconnectedDevices.append(device)
    #         if unconnectedDevices:
    #             for device in unconnectedDevices:
    #                 print(device.tags[0], "is not connected")
    #                 say("Attempting to reconnect" + device.tags[0])
    #                 if device.reconnect():
    #                     print(device.tags[0] + "reconnected")
    #                     say(device.tags[0] + "reconnected")
    #                 else: print("THIS IS PART OF A DEBUG. FAILED TO RECONNECT")
    #         else: time.sleep(5)

    # btcThread = threading.Thread(target=ensureConnection)
    # btcThread.start()
