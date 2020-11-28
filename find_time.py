import re
import datetime
import dateutil.relativedelta
import shlex

# This is a very ugly system for parsing user input in reminders

def time_to_seconds(number,unit):
    if unit != "s":
        if unit.endswith("s"):
            unit = unit[:-1]
    if unit in ["s","sec","second"]:
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
        a_month = dateutil.relativedelta.relativedelta(months=1)
        then = now + a_month
        return (then-now).total_seconds()
    # We don't really want to keep reminders for a year...
    #if unit in ["y","year"]:
    #    return number * 31536000
    return 0

def find_time(input_string):
    # First, we want to try and match time like 12h 2m 13s.
    # TODO: support written out numbers like twelve hours, two minutes and thirteen seconds.
    
    start = 0 # the time probably starts at the start of the message
    
    starting_string = "" # in case the word "in" is in the middle of the message, we should keep what comes before it
    
    in_match = re.search("(in)(?:\s+)", input_string) # does it contain "in"?
    if in_match: # we found the word "in" with a space after it!
        start = in_match.end(0) # okay, the time starts after the word in, probably
        
        temp_start = in_match.start(0) # for below
        starting_string = input_string[0:temp_start] # keep what comes before "in"! note, this includes the space which we don't need to strip
        
    valid = True
    built_time = []
    while (valid):
        substring = input_string[start:]
        #splitstring = shlex.split(string)
        number_or_time = re.search("^((\d+)|(s|sec|second|m|min|minute|h|hr|hour|d|day|w|week|mo|month)(?:s?)(?=[^a-z]|$))", substring)
        if number_or_time: # we found either a number or a valid form of time.
            built_time.append(number_or_time.group(0))
            start += number_or_time.end(0) # continue doing this, but after the thing that we found.
            if start >= len(input_string):
                substring = input_string[start:]
                valid = False
                break
            while (input_string[start:][0] == " " or input_string[start:][0] == ","):
                start += 1
        else:
            substring = input_string[start:]
            valid = False

    total_seconds = 0
    index = 0
    if len(built_time) == 0:
        return False
    while (True):
        if not built_time[index].isnumeric():
            return False
        if index + 1 >= len(built_time):
            return False

        total_seconds += time_to_seconds(int(built_time[index]), built_time[index+1])

        index += 2
        if index >= len(built_time):
            return [total_seconds,(starting_string + substring).strip()]
    return None

print(find_time("2 seconds, do something"))
print(find_time("1h do thing"))
print(find_time("12h 13m 14s do something!"))
print(find_time("3 days do smth"))
print(find_time("do thing in 1h"))
print(find_time("do thing in 1h and stuff"))
#print(find_time("do the thing tomorrow"))
#print(find_time("tomorrow do the thing"))
#print(find_time("do the thing tomorrow and stuff"))
print(find_time("1h do thing 2h"))
print(find_time("in 2 months"))
print(find_time("in 2 hours, 2 minutes play yiik"))
print(find_time("remind me to yiik in 2h"))
print(find_time("asdjfiohuiafsgdiouh"))
print(find_time("1 minute minute thingy"))
print(find_time("1 FUCkin hour"))
print(find_time("2.5 hours"))