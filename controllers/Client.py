#! /usr/bin/python3

import socket

class Client:
    serverAddress = ''
    socket = None

    def __init__(self, name, serverAddress):
        self.serverAddress = serverAddress
        self.name = name
        self.connect()

    def connect(self): #connect to server
        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(self.serverAddress)
            self.sendData(self.name)
            print("Client: Succussfully connected to server")
        except Exception as e:
            print("Client: Failed to connect to server: " + repr(e))
            self.close

    def sendData(self, command):
        self.socket.send(bytes(command, "utf-8"))

    def recvData(self):
        data = self.socket.recv(256)
        return data.decode("utf-8")

    def close(self):
        self.socket.close()
        print("Client: Closed")
