import nltk

syns = []

for entry in nltk.corpus.wordnet.synsets("yes"):
    for wird in entry.lemmas():
        print(wird.name())

# sentence = "remind me to do the dishes tomorrow at 7pm"

# tokens = nltk.word_tokenize(sentence)
# print(tokens)

# stopWords = set(nltk.corpus.stopwords.words('english'))
# cleanTokens = [w for w in tokens if not w in stopWords]
# print(cleanTokens)

# tagged = nltk.pos_tag(cleanTokens)
# print(tagged)

# chunked = nltk.ne_chunk(tagged)
# print(chunked)
