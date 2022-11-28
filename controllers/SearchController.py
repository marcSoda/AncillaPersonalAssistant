import wolframalpha

class SearchController:
    running = False
    wolfram = None
    app_id = "L7G3E5-3JKYTP6HUR"

    def __init__(self, server):
        self.wolfram = wolframalpha.Client(self.app_id)
        self.server = server
        self.run()

    def run(self):
        self.running = True

    def query(self, query):
        return next(self.wolfram.query(query).results).text
