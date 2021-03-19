import re
import datetime
import dateutil.relativedelta
import shlex
from text2digits import text2digits

# This is a very ugly system for parsing user input in reminders

t2d = text2digits.Text2Digits()

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

def find_time(input_string,ignore_in=False):
    # First, we want to try and match time like 12h 2m 13s.
    # TODO: support written out numbers like twelve hours, two minutes and thirteen seconds.

    start = 0 # the time probably starts at the start of the message

    starting_string = "" # in case the word "in" is in the middle of the message, we should keep what comes before it

    if (not ignore_in):

        in_match = re.search("(?:^|\W)(?:me\s)?(in)(?:\s+)", input_string) # does it contain "in"?
        if in_match: # we found the word "in" with a space after it!
            start = in_match.end(0) # okay, the time starts after the word in, probably

            temp_start = in_match.start(0) # for below
            starting_string = input_string[0:temp_start] # keep what comes before "in"! note, this includes the space which we don't need to strip

    valid = True
    built_time = []
    while (valid):
        substring = input_string[start:]
        #splitstring = shlex.split(string)
        # Match a number, optional space, time unit, optional "s", not alphabetical
        # For example, 1h is valid, but 1hb is not.

        # OLD REGEX: ^(\d+)\s?(s|sec|second|m|min|minute|h|hr|hour|d|day|w|week|mo|month)(?:s?)(?=[^a-z]|$)
        # That matches a number only. We have to match literally anything until a space so we can parse strings like "twelve hours"

        found_time = re.search("^([^\s]+)\s?(s|sec|second|m|min|minute|h|hr|hour|d|day|w|week|mo|month)(?:s?)(?=[^a-z]|$)", substring)
        if found_time: # we found either a number or a valid form of time.

            firstnum = None

            try:
                firstnum = int(found_time.group(1)) # Is it a digit?
            except ValueError: # Nope, it isn't
                try:
                    firstnum = int(t2d.convert(found_time.group(1))) # Well, can it be converted to one?
                except ValueError: # Also no, this is invalid
                    valid = False
                    break

            built_time.append([firstnum,found_time.group(2)])
            start += found_time.end(0) # continue doing this, but after the thing that we found.
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
        if (not ignore_in):
            return find_time(input_string,ignore_in=True)
        return False
    while (True):
        total_seconds += time_to_seconds(int(built_time[index][0]), built_time[index][1])
        index += 1
        if index >= len(built_time):
            return [total_seconds,(starting_string + substring).strip()]

    return None # This will never be reached, but some linter will probably complain about this missing.

#print(find_time("2 seconds, do something"), "true")
#print(find_time("1h do thing"), "true")
#print(find_time("12h 13m 14s do something!"), "true")
#print(find_time("3 days do smth"), "true")
#print(find_time("do thing in 1h"), "true")
#print(find_time("do thing in 1h and stuff"), "true")
##print(find_time("do the thing tomorrow"))
##print(find_time("tomorrow do the thing"))
##print(find_time("do the thing tomorrow and stuff"))
#print(find_time("1h do thing 2h"), "true")
#print(find_time("in 2 months"), "true")
#print(find_time("in 2 hours, 2 minutes do something"), "true")
#print(find_time("remind me to something in 2h"), "true")
#print(find_time("asdjfiohuiafsgdiouh"), "false")
#print(find_time("1 minute minute thingy"), "true")
#print(find_time("1 HEcking hour"), "false")
#print(find_time("2.5 hours"), "false")
#print(find_time("2 months https://twitter.com/NeveGlaciers/status/1334597817822826497?s=20 is this true? is she on your kin list now?"), "true")
#print(find_time("5h stream bloons or something your twitch channel is literally rotting in the dirt"), "true")
#print(find_time("me in 5h to something"),"true")
#print(find_time("5h 2s h"),"true")
#print(find_time("twelve hours"),"true")