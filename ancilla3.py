import pyttsx3
from SnowboyDependencies import snowboydecoder_op as sb
import os
import time

intent_path = "machineLearning/intents.json"
vocab_path = "machineLearning/vocabulary.json"
model_path = "machineLearning/model.h5"
ding_path = "SnowboyDependencies/resources/ding.wav"
dong_path = "SnowboyDependencies/resources/dong.wav"
hotword_path = "SnowboyDependencies/Wumbo.pmdl"


detector = sb.HotwordDetector(hotword_path, sensitivity=0.42)

#setup pyttsx engine
engine = pyttsx3.init("espeak")

def wait_for_command():
    detector.wait_for_hotword(detected_callback=detected_callback)
    
def detected_callback():
    sb.play_audio_file(ding_path) 
    text = detector.get_stt()
    print(text)
    say(text)
    process(text)

def say(text):
    engine.say(text)
    engine.runAndWait()  
    
def process(text):
    if 'how' in text:
        say("are you sure")
        print(detector.get_stt())      
    # detector.terminate()
    # if text == "Failure":
    #     say(text)
    # else:
    #     intent = get_intent(text)
    #     if intent == "reminder_db":
    #         rem = Reminder(text)
    #         if rem.try_parse_from_text():
    #             label = rem.get_label()
    #             say("Are you sure you want to set a reminder to " + label)
    #             answer = get_text()
    #             make_sure(rem, answer)
    #         else:
    #             if not rem.has_label():
    #                 say("What is the reminder?")
    #                 label = get_text()
    #                 # if label
    #                 say("Are you sure you want to set a reminder to " + label)
    #                 answer = get_text()
    #                 make_sure(rem, answer)
    #     else: say("There was an error") #temporary
    # wait_for_command()  

wait_for_command()
detector.terminate()