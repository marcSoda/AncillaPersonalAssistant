import nltk
import numpy
import tensorflow as tf
import json

stopwords = nltk.corpus.stopwords.words('english')
num_epochs = 600
intent_path = "intents.json"
model_path = "model.h5"

#EXTRACT DATA FROM JSON FILE
with open(intent_path) as file: #load json file (training data)
    data = json.load(file)
tokens = []
tags = [] #these appear to be the same list
raw_tokens = []
raw_tags = [] #these appear to be the same list
for intent in data['intents']:
    for pattern in intent['patterns']:
        words = nltk.word_tokenize(pattern)
        words = [word for word in words if '*' not in word and word not in stopwords]
        tokens.extend(words)
        raw_tokens.append(words)
        raw_tags.append(intent["tag"])

    if intent['tag'] not in tags:
        tags.append(intent['tag'])
tokens = sorted(list(set(tokens)))
tags = sorted(tags)

#PREPARE TRAINING DATA
training = []
output = []
out_empty = [0 for _ in range(len(tags))]

for x, doc in enumerate(raw_tokens):
    binary_token_array = []
    words = [word.lower() for word in doc]
    for token in tokens:
        if token in words:
            binary_token_array.append(1)
        else:
            binary_token_array.append(0)
    output_row = out_empty[:]
    output_row[tags.index(raw_tags[x])] = 1
    training.append(binary_token_array)
    output.append(output_row)

training = numpy.array(training)
output = numpy.array(output)

#CREATE, TRAIN, AND SAVE MODEL
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(len(training[0]),
          activation=tf.nn.relu,
          input_shape=(len(training[0]),)))
          # input_shape=(None, len(training[0]))))
model.add(tf.keras.layers.Dense(8, activation=tf.nn.relu))
model.add(tf.keras.layers.Dense(8, activation=tf.nn.relu))
model.add(tf.keras.layers.Dense(len(output[0]),
          activation=tf.nn.softmax))
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])
print(model.summary())

model.fit(training, output, epochs=num_epochs)
model.save(model_path)
