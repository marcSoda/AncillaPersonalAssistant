#! /usr/bin/python3
import pyttsx3
from snowboy import snowboydecoder_op as sb
from controllers.Server import *
import threading
import select
import time
import os

def listenForConnections():
    while 1:
        try:
            newClientName = server.listen()
            if newClientName == "":
                say("Failed to initialize socket")
                continue
            say("Initialized " + newClientName + " socket")
        except Exception as e:
            print("Exception in listenForConnections: " + repr(e))

def listenForResponses():
    while 1:
        try:
            socket_list = server.clients.values()
            read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [], .5)
            for s in read_sockets:
                response = server.recvData(s)
                if ("SIGKILL" in response): kill(s)
                else: say(response)
        except Exception as e:
            print("Exception in listenForResponses: " + repr(e))

def say(text):
    print(text)
    with lock:
        engine.say(text)
        engine.runAndWait()

def detected_callback():
    with lock: sb.play_audio_file(ding_path)
    text = detector.get_stt().lower()
    with lock: sb.play_audio_file(dong_path)
    operate(text)

def operate(text):
    print("TEXT: " + text)
    split = text.split(' ', 1) #split off the first word
    if len(split) <= 1:
        say("Invalid command length")
        return
    toSock = split[0]
    command = split[1]

    if toSock == "start" or toSock == "restart":
        restart(command)
        return
    if toSock not in server.clients.keys():
        toSock = "bluetooth"
    try: server.sendData(toSock, command)
    except:
        say("Problem with " + toSock + " socket. Attempting to restart.")
        restart(toSock)

def kill(clientSocketOrName):
    deadClient = server.kill(clientSocketOrName)
    say("Successfully killed " + deadClient + " socket")

def restart(clientName):
    if clientName in server.clients.keys():
        kill(clientName)
    if clientName not in systemdClients.keys():
        say(clientName + " is not a valid socket name.")
        return
    os.system("sudo systemctl restart " + systemdClients[clientName])

#setup hotword detector
snowboy_resource_path = "./snowboy/resources/"
ding_path = snowboy_resource_path + "ding.wav"
dong_path = snowboy_resource_path + "dong.wav"
hotword_path = snowboy_resource_path + "models/computer.umdl"
detector = sb.HotwordDetector(decoder_model=hotword_path, sensitivity=.50, audio_gain=2)
#setup pyttsx engine
engine = pyttsx3.init()
#setup server
server = Server("/tmp/socket")
#setup threads
connectionListener = threading.Thread(target=listenForConnections)
connectionListener.start()
responseListener = threading.Thread(target=listenForResponses)
responseListener.start()
lock = threading.Lock()
#systemd client service names
systemdClients = {}
systemdClients["bluetooth"] = "ancillaBluetooth.service"
systemdClients["alarm"] = "ancillaAlarm.service"

say("Initialized speech")
detector.wait_for_hotword(detected_callback=detected_callback)
detector.terminate()
