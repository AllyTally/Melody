import json

config = {}

def read_config():
    global config
    with open("config.json", encoding='utf-8') as file:
        file_contents = file.read()
        config = json.loads(file_contents)
    required_values = ["token","owners"]
    default_values = {"invokers": ["!"]}
    failed = False
    for item in required_values:
        if not item in config:
            print(item + " is missing from config.json.")
            failed = True
    if failed:
        sys.exit()
    for key, value in default_values.items():
        if not key in config:
            print(key + " is missing from config.json. The default value(s) will be used.")
            config[key] = value

read_config()