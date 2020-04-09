import json

intent_path = "common_task_phrases.json"

reminder_common_phrases = []
calendar_common_phrases = []
alarm_common_phrases = []
list_common_phrases = []
password_common_phrases = []
power_common_phrases = []
with open(intent_path) as file: #load json file (training data)
    data = json.load(file)
for task in data['tasks']:
    if task['tag'] == 'reminder_db':
        for phrase in task['phrases']:
            reminder_common_phrases.append(phrase)

class Reminder:
    label = None
    text = None
    tokens = None #TODO: do we need the tokens? reminder might not need them, but some tasks will

    def __init__(self, text):
        self.text = text
        # self.tokens = tokens

    #determines label if possible and returns true. if not, returns false
    def try_parse_from_text(self):
        for phrase in reminder_common_phrases:
            if phrase in self.text:
                remaining_text = self.text.replace(phrase, '')
                if len(remaining_text) > 0:
                    self.label = remaining_text
                    return True
                else: 
                    return False
        return False

    def get_label(self): #label should never be null here
        return self.label

    def set_label(self, label):
        self.label = label

    def has_label(self):
        if self.label is None:
            return False
        else:
            return True

    def add_to_database(self):
        pass

#TODO: for future tasks, get ints and dates etc using nltk

# if __name__ == "__main__":
#     text = "set a reminder to take out the trash"
#     new_reminder(text, None)
