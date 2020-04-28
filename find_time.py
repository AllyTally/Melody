import re
import datetime

# This is a very ugly system for parsing user input in reminders

def time_to_seconds(number,unit):
    if unit in ["s","second"]:
        return number
    if unit in ["m","min","minute"]:
        return number * 60
    if unit in ["h","hr","hour"]:
        return number * 3600
    if unit in ["d","day"]:
        return number * 86400
    if unit in ["w","week"]:
        return number * 604800
    if unit in ["mo","month"]:
        now = datetime.datetime.now()
        then = now.replace(month=now.month + number)
        return (then-now).total_seconds()
        #return number * 2592000 # This should definitely be changed--months aren't always 30 days, sadly
    # We don't really want to keep reminders for a year...
    #if unit in ["y","year"]:
    #    return number * 31536000
    return 0

def find_time(input):
    # First, we want to try and match time like 12h 2m 13s.
    # TODO: support written out numbers like twelve hours, two minutes and thirteen seconds.
    result = list(re.finditer(r"(?:(?:in\s*)?)(\d+)\s*(s|second|m|min|minute|h|hr|hour|d|day|w|week|mo|month)(?:s?)(?=[^a-z]|$)", input))
    if result != []:
        # Cool, we got a match!
        total_seconds = 0
        words = []
        for match in result:
            words.append(match.group(0))
            groups = match.groups()
            total_seconds += time_to_seconds(int(groups[0]),groups[1]) # Transform each time (ex: 2m) into seconds (ex: 120)
        return [total_seconds,words]
    elif "tomorrow" in input:
        return [86400,["tomorrow"]] # 24 hours in seconds
    # TODO: add more cases
    return None

#print(find_time("2 seconds, do something"))
#print(find_time("1h do thing"))
#print(find_time("12h 13m 14s do something!"))
#print(find_time("3 days do smth"))
#print(find_time("do thing in 1h"))
#print(find_time("do thing in 1h and stuff"))
#print(find_time("do the thing tomorrow"))
#print(find_time("tomorrow do the thing"))
#print(find_time("do the thing tomorrow and stuff"))
#print(find_time("1h do thing 2h"))