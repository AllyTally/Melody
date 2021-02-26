import time
import sys
import config

def convert_to_bright(color):
    bold_colors = ["a","b","c","d","e","f","g","h"]
    if color in bold_colors:
        return bold_colors.index(color) + 60
    return color

def color(fg=None, bg=None):
    if fg == "reset":
        return "\033[0m";
    fg = convert_to_bright(fg)
    bg = convert_to_bright(bg)
    if fg and bg:
        return f"\033[{30 + int(fg)};{40 + int(bg)}m"
    if fg:
        return f"\033[{30 + int(fg)}m"
    if bg:
        return f"\033[{40 + int(bg)}m"
    return ""

def log(text):
    print(color(config.config['color-default']) + str(text) + "\033[0m")

def info(text):
    print(f"{color(config.config['color-info'])}[INFO] {str(text)}\033[0m")

def warn(text):
    print(f"{color(config.config['color-warn'])}[WARN] {str(text)}\033[0m")

def error(text):
    print(f"{color(config.config['color-error'])}[ERROR] {str(text)}\033[0m")
