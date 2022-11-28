# import wolframalpha

# class SearchController:
#     running = False
#     wolfram = None
#     app_id = "L7G3E5-3JKYTP6HUR"

#     def __init__(self, server):
#         self.wolfram = wolframalpha.Client(self.app_id)
#         self.server = server
#         self.run()

#     def run(self):
#         self.running = True

#     def query(self, query):
#         res = self.wolfram.query(query)
#         answer = next(res.results).text
#         print(answer)
#         return answer

import wolframalpha
# Taking input from user
question = input('Question: ')
# App id obtained by the above steps
app_id = "L7G3E5-3JKYTP6HUR"
# Instance of wolf ram alpha
# client class
client = wolframalpha.Client(app_id)

# Stores the response from
# wolf ram alpha
res = client.query(question)

# Includes only text from the response
answer = next(res.results).text

print(answer)
