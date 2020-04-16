print("Loading...")
import pyttsx3
from SnowboyDependencies import snowboydecoder_op as sb
import os
import time
import pyttsx3
import json
from task_engine import Reminder
import numpy
import nltk
import tensorflow as tf

intent_path = "machineLearning/intents.json"
vocab_path = "machineLearning/vocabulary.json"
model_path = "machineLearning/model.h5"
ding_path = "SnowboyDependencies/resources/ding.wav"
dong_path = "SnowboyDependencies/resources/dong.wav"
hotword_path = "SnowboyDependencies/Wumbo.pmdl"
key = '63NBK27X2KH7IW6SBO3LDC644SF7MGJ5'

#setup snowboy
detector = sb.HotwordDetector(hotword_path, sensitivity=0.42)

#setup pyttsx engine
engine = pyttsx3.init("espeak")

#prepare basic vocabulary for yes, no, and cancel
yes_words = []
no_words = []
cancel_words = []
with open(vocab_path) as file: #load json file (training data)
    data = json.load(file)
for word_list in data['word_list']:
    if word_list['tag'] == 'yes_words':
        for word in word_list['words']:
            yes_words.append(word)
    if word_list['tag'] == 'no_words':
        for word in word_list['words']:
            no_words.append(word)
    if word_list['tag'] == 'cancel_words':
        for word in word_list['words']:
            cancel_words.append(word)
            
#prepare machine learning model
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
    
def detected_callback():
    sb.play_audio_file(ding_path) 
    text = detector.get_stt(key)
    print(text)
    process(text)

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
    result_index = numpy.argmax(results)
    if results[0,result_index] > .7:
        tag = tags[result_index]
        print(numpy.round(results, 2), tag)
        return tag
    else:
        return "I didn't get that" 
    
def process(text):
    if text == None:
        print("There was an arror")
        say("There was an error")
    else:
        intent = get_intent(text)
        if intent == "reminder_db":
            rem = Reminder(text)
            if rem.try_parse_from_text():
                label = rem.get_label()
                say("Are you sure you want to set a reminder to " + label)
                answer = get_text()
                make_sure(rem, answer)
            else:
                if not rem.has_label():
                    say("What is the reminder?")
                    label = get_text()
                    # if label
                    say("Are you sure you want to set a reminder to " + label)
                    answer = get_text()
                    make_sure(rem, answer)
        else: say("There was an error") #temporary

print("ready")
detector.wait_for_hotword(detected_callback=detected_callback)
detector.terminate()