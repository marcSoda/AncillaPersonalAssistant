import nltk
import numpy
import tensorflow as tf
import json

stopwords = nltk.corpus.stopwords.words('english')
num_epochs = 600
vocab_path = "vocabulary.json"
intent_path = "intents.json"
model_path = "model.h5"

#vocab word lists
create_words = []
delete_words = []
show_words = []
with open(vocab_path) as file: #load json file (training data)
    data = json.load(file)
for word_list in data['word_list']:
    if word_list['tag'] == 'create_words':
        for word in word_list['words']:
            create_words.append(word)
    if word_list['tag'] == 'delete_words':
        for word in word_list['words']:
            delete_words.append(word)
    if word_list['tag'] == 'show_words':
        for word in word_list['words']:
            show_words.append(word)

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
        # words = [word for word in words if '*' not in word and word not in stopwords]
        words = [word for word in words if word not in stopwords]   
        
        for word in words:
            if word == '*create_word':
                for c_word in create_words:
                    new_words = [c_word if word == '*create_word' else word for word in words]
                    words.append(new_words)
        
        for w in words:
            tokens.extend(w)
            raw_tokens.append(w)
        raw_tags.append(intent["tag"])

    if intent['tag'] not in tags:
        tags.append(intent['tag'])
tokens = sorted(list(set(tokens)))
tags = sorted(tags)

# print(tokens)
# print(tags)
# print(raw_tokens)
# print(raw_tags)

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

model = tf.keras.models.load_model(model_path)
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

# for word in words:
        #     if word == '*create_word':
        #         for c_word in create_words:
        #             new_words = words[:]
        #             new_words = [c_word if word == '*create_word' else word for word in words]
        #         tokens.extend(new_words)
        #         raw_tokens.append(new_words)
        # raw_tags.append(intent["tag"])