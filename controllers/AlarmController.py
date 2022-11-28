import time
import datetime
import threading
import os
import pickle

repeat = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

class AlarmController:
    alarms = {}
    running = False
    clockThread = None
    stop = False

    def __init__(self, server):
        self.server = server
        self.run()
        try:
            with open("../alarms.pickle", "rb") as p:
                self.alarms = pickle.load(p)
        except Exception:
            print("AlarmContriller.__init__: bad pickle: nonfatal")

    def run(self):
        self.running = True
        self.clockThread = threading.Thread(target = self.clock)
        self.clockThread.daemon = True #kill thread when main thread closes
        self.clockThread.start()

    def clock(self):
        while 1:
            time.sleep(1)
            dtNow = datetime.datetime.now()
            currentHour = dtNow.strftime("%I")
            currentMinute = dtNow.strftime("%M")
            currentAmpm = dtNow.strftime("%p").lower()
            currentDay = dtNow.strftime("%A").lower()
            for a in list(self.alarms.values()): #force a copy of the values to be made so there are no errors when iterating
                if (int(currentHour) == int(a.hour) and
                    int(currentMinute) == int(a.minute) and
                    currentAmpm == a.ampm and
                    (currentDay in a.days or not a.repeat)):
                    self.server.sendData("SIGSEND: bluetooth alarmlight on") #send a signal to the server to turn on all the lights with the 'alarmlight' tag
                    while not self.stop: #Until alarm is stopped, ring 3 times, wait 5 seconds, then repeat
                        for i in range(3): os.system("aplay ../alarm.wav > /dev/null 2>&1")
                        time.sleep(5)
                    self.stop = False
                    if not a.repeat: del self.alarms[a.name]
                    time.sleep(60) #sleep for a minute so alarm is not triggered again

    def writePickle(self):
        try:
            with open("../alarms.pickle", "wb") as p:
                pickle.dump(self.alarms, p)
        except:
            print("AlarmController.addAlarm: bad pickle: nonfatal")

    def addAlarm(self, tokens):
        alarm = None
        try:
            alarm = Alarm(tokens)
        except Exception as e:
            self.server.sendData("Invalid Alarm Entry")
            return
        self.alarms[alarm.name] = alarm
        self.writePickle()
        self.server.sendData("Added alarm: " + alarm.toSpeechString())

    def stopAlarm(self):
        self.stop = True

    def listAlarms(self):
        if len(self.alarms) == 0:
            self.server.sendData("No alarms")
        for a in list(self.alarms.values()): #force a copy of the values to be made so there are no errors when iterating
            self.server.sendData(a.toSpeechString())

    def deleteAlarm(self, tokens):
        name = ' '.join(tokens)
        try:
            del self.alarms[name]
        except Exception as e:
            self.server.sendData("Invalid Alarm Name")
            return
        self.writePickle()
        self.server.sendData("Removed alarm: " + name)

    def clearAlarms(self):
        self.alarms = {}
        self.writePickle()
        self.server.sendData("Cleared alarms")

class Alarm:
    hour = ""
    minute = ""
    ampm = ""
    days = []
    name = ""
    repeat = False

    def __init__(self, tokens):
        if not self.fillParams(tokens):
            raise ValueError("Invalid Alarm Entry")

    #TODO: this function is not checked enough. ex: ampm could be any string
    def fillParams(self, tokens):
        try:
            hm = tokens.pop(0)
            if ":" in hm: #if time contains a ':' ie 3:01 am
                hm = hm.split(':')  #first entry is always hour:minute
                self.hour = hm[0]
                self.minute = hm[1]
            else: #if time does not contain a ':' ie 3 am
                self.hour = hm
                self.minute = "00"
            self.ampm = tokens.pop(0).replace('.', '') #ensure ampm has no periods
            self.days = []
            for t in tokens[:]:            #iterate over a copy of the remaining tokens
                if t in repeat:      #if the token is a day of the week
                    self.repeat = True
                    self.days.append(t)    #add it to the list of days
                    tokens.remove(t)       #remove it from the remaining tokens
            self.name = ' '.join(tokens)   #the alarm of the name is a string of the remaining tokens separated by a space
        except Exception as e:
            print("AlarmController.Alarm.fillParams: Invalid alarm entry")
            return False
        return True

    def toSpeechString(self): #return a string that is designed to be spoken
        timeString = self.hour + ":" + self.minute + " " + self.ampm
        daysString = ' '.join(self.days)
        if self.repeat:
            return self.name + ". " + timeString + " on " + daysString + "..."
        return self.name + ". " + timeString + "..."
