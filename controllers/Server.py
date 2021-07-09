#! /usr/bin/python3
import socket
import os

class Server:
    address = ''
    clients = {} # dict of clients name:socket
    thisSocket = None

    def __init__(self, address):
        self.address = address
        if os.path.exists(address): os.unlink(address)

    def bind(self):
        try:
            self.thisSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.thisSocket.bind(self.address)
            print("Server: Bound")
        except:
            print("Server: Failed to open StreamCollector")

    def listen(self):
        newClientName = ""
        try:
            self.thisSocket.listen(0)
            newClient, address = self.thisSocket.accept()
            newClient.setblocking(0) #recv and send will return immediately
            newClientName = newClient.recv(256).decode("utf-8")
            self.clients[newClientName] = newClient
        except Exception as e:
            print("Exception in Server.listen " + repr(e))
        return newClientName

    def sendData(self, clientName, command):
        self.clients[clientName].sendall(bytes(command, "utf-8"))

    def recvData(self, clientName): #listen for response based on client name
        #todo: receive data as a buffer rather than max 256 bytes
        data = self.clients[clientName].recv(256)
        return data.decode("utf-8")
    def recvData(self, clientSocket): #listen for response based on clientsocket
        #todo: receive data as a buffer rather than max 256 bytes
        data = clientSocket.recv(256)
        return data.decode("utf-8")

    def kill(self, clientName):
        try:
            self.clients[clientName].close()
            del self.clients[clientName]
        except Exception as e:
            print("Server.kill: Exception when attempting to kill client by client name"+ repr(e))
    def kill(self, clientSocket):
        try:
            clientName = list(self.clients.keys())[list(self.clients.values()).index(clientSocket)]
            self.clients[clientName].close()
            del self.clients[clientName]
        except Exception as e:
            print("Server.kill: Exception when attempting to kill client by clientSocket"+ repr(e))

    def close(self):
        try:
            for s in self.clients:
                s.close()
            self.thisSocket.close()
            print("Server: Closed")
        except:
            print("Server: Failed to close")
