import json

persistent = {}

def read_persistent():
    global persistent
    with open("persistent.json", encoding='utf-8') as file:
        file_contents = file.read()
        persistent = json.loads(file_contents)
    default_values = {"restart_message": None, "restart_timestamp": 0, "reminders": {}}
    for key, value in default_values.items():
        if not key in persistent:
            print(key + " is missing from persistent.json. The default value(s) will be used.")
            persistent[key] = value

def save():
    global persistent
    with open('persistent.json', 'w') as outfile:
        json.dump(persistent, outfile, indent=4)