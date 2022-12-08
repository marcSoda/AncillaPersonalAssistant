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
        self.bind()

    def bind(self):
        try:
            self.thisSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.thisSocket.bind(self.address)
            print("Server: Bound")
        except:
            print("Server: Failed to bind socket to " + self.address)

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

    def recvData(self, clientSocketOrName): #listen for response based on client socket or name
        #todo: receive data as a buffer rather than max 256 bytes
        data = None
        if clientSocketOrName in self.clients.keys():
            data = self.clients[clientName].recv(256)
        elif clientSocketOrName in self.clients.values():
            data = clientSocketOrName.recv(256)
        return data.decode("utf-8")

    def getClientName(self, clientSocket):
        return clientName

    def kill(self, clientSocketOrName):
        clientName = None
        if clientSocketOrName in self.clients.keys():
            clientName = clientSocketOrName
        elif clientSocketOrName in self.clients.values():
            clientName = list(self.clients.keys())[list(self.clients.values()).index(clientSocketOrName)]
        else:
            raise Exception("Socket does not exist in Socket.clients")
        try:
            self.clients[clientName].close()
            del self.clients[clientName]
        except Exception as e:
            print("Server.kill: Exception when attempting to kill client by client name"+ repr(e))
        return clientName

    def close(self):
        try:
            for s in self.clients:
                s.close()
            self.thisSocket.close()
            print("Server: Closed")
        except:
            print("Server: Failed to close")
