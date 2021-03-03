import json
import sys

config = {}

required_values = [
    "token",
    "owners"
]

default_values = {
    "invokers": ["!"],
    "db-name": "melody",
    "db-host": "localhost",
    "db-port": "5432",
    "db-auth": False,
    "db-user": "username",
    "db-pass": "password",
    "color-default": "7",
    "color-info": "g",
    "color-error": "b",
    "color-warning": "d",
    "color-background": "0"
}

def read_config():
    global config
    with open("config.json", encoding='utf-8') as file:
        file_contents = file.read()
        config = json.loads(file_contents)

    failed = False
    for item in required_values:
        if not item in config:
            print("CONFIG: " + item + " is missing from config.json.")
            failed = True
    if failed:
        sys.exit()
    for key, value in default_values.items():
        if not key in config:
            print("CONFIG: " + key + " is missing from config.json. The default value(s) will be used.")
            config[key] = value

read_config()