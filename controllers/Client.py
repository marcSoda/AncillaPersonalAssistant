#! /usr/bin/python3

import time
import socket

class Client:
    serverAddress = ''
    socket = None

    def __init__(self, name, serverAddress):
        self.serverAddress = serverAddress
        self.name = name
        while not self.connect():
            print("Client.__init__(): Failed to connect. Trying again.")
            time.sleep(1)

    def connect(self): #connect to server
        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(self.serverAddress)
            self.sendData(self.name)
        except Exception as e:
            self.close
            return False
        print("Client: Succussfully connected to server")
        return True

    def sendData(self, command):
        self.socket.send(bytes(command, "utf-8"))

    def recvData(self):
        data = self.socket.recv(256)
        return data.decode("utf-8")

    def close(self):
        self.socket.close()
        print("Client: Closed")
