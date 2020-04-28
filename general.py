import discord
from common import command, fetch, send
import urllib
import find_time
from humanfriendly import format_timespan
import time
import persistent

@command()
async def calc(bot, message, **kwargs):
    if kwargs["string_arguments"] == None:
        await send(message, "Please enter a math equation.")
        return
    url = "https://api.mathjs.org/v4/?expr=" + urllib.parse.quote(kwargs["string_arguments"])
    data = await fetch(url)
    await send(message, data.decode())

@command()
async def remind(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    if args == None:
        await send(message, "Please enter a valid time. Examples: `tomorrow`, `10h`, `3 days`")
        return
    dates = find_time.find_time(args)
    if dates == None:
        await send(message, "Please enter a valid time. Examples: `tomorrow`, `10h`, `3 days`")
        return
    remindertext = args
    for i in dates[1]:
        remindertext = remindertext.replace(i,"",1)
    remindertext = remindertext.strip()
    seconds = dates[0]
    if seconds < 1 or seconds >= 31536000:
        await send(message, "Please enter a valid time. Examples: `tomorrow`, `10h`, `3 days`")
        return
    readable_time = format_timespan(seconds)
    reminder = {
        "timestamp": round(time.time()) + seconds,
        "called_timestamp": round(time.time()),
        "text": remindertext,
        "user_id": message.author.id,
        "channel_id": message.channel.id,
        "message_id": message.id,
        "guild_id": "@me"
    }
    if remindertext == "":
        reminder["text"] = "(No reminder text.)"
    if message.guild:
        reminder["guild_id"] = message.guild.id
    persistent.persistent["reminders"][message.id] = reminder
    if remindertext == "":
        await send(message, f"{message.author.mention}, I'll mention you in {readable_time}.")
    else:
        await send(message, f"{message.author.mention}, in {readable_time}: {remindertext}")

@command()
async def reminders(bot, message, **kwargs):
    reminders = 0
    em = discord.Embed(title='Your reminders:')
    for key,reminder in persistent.persistent["reminders"].items():
        if reminder["user_id"] == message.author.id:
            reminders += 1
            seconds = round(reminder["timestamp"] - time.time())
            readable_time = format_timespan(seconds)
            em.add_field(name=f"{key}: In {readable_time}", value=f"[{reminder['text']}](https://discordapp.com/channels/{str(reminder['guild_id'])}/{str(reminder['channel_id'])}/{str(reminder['message_id'])})",inline=False)
    if reminders == 0:
        await send(message, "You have no reminders.")
        return
    em.set_footer(text="You can cancel a reminder using m!cancelreminder <reminder id>")
    await send(message, embed=em)

@command()
async def cancelreminder(bot, message, **kwargs):
    try:
        id = int(kwargs["arguments"][0])
    except ValueError:
        await send(message, "Invalid reminder ID.")
        return
    if id in persistent.persistent["reminders"]:
        if persistent.persistent["reminders"][id]["user_id"] == message.author.id:
            persistent.persistent["reminders"].pop(id)
            await send(message, "Canceled reminder.")
        else:
            await send(message, "Invalid reminder ID.")
    else:
        await send(message, "Invalid reminder ID.")
        return
