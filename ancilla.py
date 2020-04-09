import speech_recognition as sr
import pyttsx3
import os
import json
from task_engine import Reminder
import numpy
import nltk
import tensorflow as tf
from SnowboyDependencies import snowboydecoder
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
from contextlib import contextmanager

intent_path = "machineLearning/intents.json"
model_path = "machineLearning/model.h5"
ding_path = "SnowboyDependencies/resources/ding.wav"
dong_path = "SnowboyDependencies/resources/dong.wav"
hotword_path = "SnowboyDependencies/Wumbo.pmdl"

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt): pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
@contextmanager
def no_alsa_error():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

with no_alsa_error():
    detector = snowboydecoder.HotwordDetector(hotword_path, sensitivity=0.42)
def get_wav_data(self): #MONKEY-PATCH function
    data = b''.join(self.recordedData)
    return data
snowboydecoder.HotwordDetector.saveMessage = get_wav_data

r = sr.Recognizer()
r.pause_threshold = 0.5 #seconds of non-speaking audio before a phrase is considered complete
r.phrase_threshold = 0.2 #minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
r.non_speaking_duration = .3 # seconds of non-speaking audio to keep on both sides of the recording

engine = pyttsx3.init("espeak")

stopwords = nltk.corpus.stopwords.words('english')
tokens = []
tags = []
with open(intent_path) as file: #load json file (training data)
    data = json.load(file)
for intent in data['intents']:
    for pattern in intent['patterns']:
        words = nltk.word_tokenize(pattern)
        words = [word for word in words if '*' not in word and word not in stopwords]
        tokens.extend(words)
    if intent['tag'] not in tags:
        tags.append(intent['tag'])
tokens = sorted(list(set(tokens)))
tags = sorted(tags)

model = tf.keras.models.load_model(model_path)

def wait_for_command():
    detector.start(audio_recorder_callback=audio_recorder_callback,
                detected_callback=detected_callback,
                silent_count_threshold=5,
                sleep_time=0.01)

def detected_callback(): #plays a ding after hotword detect
    print("recording...")
    snowboydecoder.play_audio_file(ding_path)

def audio_recorder_callback(data): #used after wakeword only
    snowboydecoder.play_audio_file(dong_path)
    print("converting audio to text...")
    ad = sr.AudioData(data, 16000, 2)
    text = "Failure"
    try:
        text = r.recognize_google(ad).lower()
    except sr.UnknownValueError:
        print("Sorry, I'm retarded")
    except sr.RequestError:
        print("Problem with Google")
    print(text)
    process(text)

def get_text(): #used when bot asks questions
    #increased sample rate to increase audio quality DOES NOT WORK AT DEFAULT RATE
    with no_alsa_error():
        with sr.Microphone(sample_rate = 48000) as source:
            # r.adjust_for_ambient_noise(source)
            snowboydecoder.play_audio_file(ding_path)
            audio = r.listen(source)
    snowboydecoder.play_audio_file(dong_path)
    text = "Failure"
    try:
        text = r.recognize_google(audio).lower()
    except sr.UnknownValueError:
        print("Sorry, I'm retarded")
    except sr.RequestError:
        print("Problem with Google")
    print(text)
    return text

def say(text):
    engine.say(text)
    engine.runAndWait()

def get_intent(text):
    # prepate input
    binary_token_array = [0 for _ in range(len(tokens))]
    text_tokens = nltk.word_tokenize(text)
    stopwords = nltk.corpus.stopwords.words('english')
    text_tokens = [token for token in text_tokens if token not in stopwords]
    for token in text_tokens:
        for i, word in enumerate(tokens):
            if word == token:
                binary_token_array[i] = 1
    arr = numpy.array(binary_token_array)
    matrix = numpy.matrix(arr)

    results = model.predict([matrix])
    print(numpy.round(results, 2))
    result_index = numpy.argmax(results)
    if results[0,result_index] > .7:
        tag = tags[result_index]
        print(tag)
        return tag
    else:
        return "I didn't get that"

def process(text):
    detector.terminate()
    if text == "Failure":
        say(text)
    else:
        intent = get_intent(text)
        if intent == "reminder_db":
            rem = Reminder(text)
            if rem.try_parse_from_text():
                label = rem.get_label()
                say("Are you sure you want to set a reminder to " + label)
                answer = get_text()
                if answer == 'yes':
                    rem.add_to_database()
                    say("Reminder set")
                else: #TODO: perhaps add a loop to rather than just exiting
                    say("Reminder Not Set")
            else:
                if not rem.has_label():
                    say("What is the reminder?")
                    label = get_text()
                    say("Are you sure you want to set a reminder to " + label)
                    answer = get_text()
                    if answer == 'yes':
                        rem.add_to_database()
                        say("Reminder set")
                    else: #TODO: perhaps add a loop to rather than just exiting
                        say("Reminder Not Set")
        else: say("There was an error") #temporary
    wait_for_command()

wait_for_command()
detector.terminate()