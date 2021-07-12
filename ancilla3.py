#! /usr/bin/python3
import pyttsx3
from snowboy import snowboydecoder_op as sb
from controllers.Server import *
import threading
import select
import time

def listenForConnections():
    while 1:
        try:
            newClientName = server.listen()
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
                if ("SIGKILL" in response): server.kill(s)
                else: say(response)
        except Exception as e:
            print("Exception in listenForResponses: " + repr(e))

def say(text):
    print(text)
    with lock:
        engine.say(text)
        engine.runAndWait()

def detected_callback():
    sb.play_audio_file(ding_path)
    text = detector.get_stt()
    print("TEXT: " + text)
    server.sendData("bluetooth", text)
    sb.play_audio_file(dong_path)

#setup hotword detector
snowboy_resource_path = "./snowboy/resources/"
ding_path = snowboy_resource_path + "ding.wav"
dong_path = snowboy_resource_path + "dong.wav"
hotword_path = snowboy_resource_path + "models/computer.umdl"
detector = sb.HotwordDetector(decoder_model=hotword_path, sensitivity=.38, audio_gain=2)
#setup pyttsx engine
engine = pyttsx3.init()
#setup server
server = Server("/tmp/socket")
server.bind()
#setup threads
connectionListener = threading.Thread(target=listenForConnections)
connectionListener.start()
responseListener = threading.Thread(target=listenForResponses)
responseListener.start()
lock = threading.Lock()

say("Initialized speech")
detector.wait_for_hotword(detected_callback=detected_callback)
detector.terminate()
