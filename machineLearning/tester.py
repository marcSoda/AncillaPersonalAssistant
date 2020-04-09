import nltk
import numpy
import tensorflow as tf
import json

#TODO: REWRITE THIS LATER WHEN YOU REWRITE trainer.py

intent_path = "intents.json"
modelPath = "model.h5"
stopwords = nltk.corpus.stopwords.words('english')


def prepare_input(input, tokens): #prep nn input
    binary_token_array = [0 for _ in range(len(tokens))]
    input_tokens = nltk.word_tokenize(input)
    input_tokens = [token for token in input_tokens if token not in stopwords]
    for token in input_tokens:
        for i, word in enumerate(tokens):
            if word == token:
                binary_token_array[i] = 1
    arr = numpy.array(binary_token_array)
    arrM = numpy.matrix(arr)
    return arrM

#extract json data
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

#chat
print(tokens)
print("tags", tags)

model = tf.keras.models.load_model(modelPath)
print("tests inputs returns intent. input test input now")
while True:
    inp = input("You: ")
    results = model.predict([prepare_input(inp, tokens)])
    print(numpy.round(results, 2))
    result_index = numpy.argmax(results)
    if results[0,result_index] > .7:
        tag = tags[result_index]
        print(tag)
    else:
        print("I didn't get that.")
