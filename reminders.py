import discord
from common import command, reply
from client import bot
import find_time
from humanfriendly import format_timespan
import math
import time
import tasks
import find_time
import logs
import database

current_reminders = {}


def fetch_reminders():
    reminders = database["reminders"]
    return list(reminders.find())

def create_all_reminders():
    logs.info("Creating reminder tasks.")
    for reminder_id in database.fetch_reminders():
        logs.info("Creating " + str(reminder_id))
        current_reminders[reminder_id] = bot.loop.create_task(tasks.check_reminder(reminder_id))
        logs.info("Created " + str(reminder_id) + " successfully")

@command()
async def remind(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    if args == None:
        await reply(message, "Please enter a valid time. Examples: `tomorrow`, `10h`, `3 days`")
        return
    dates = find_time.find_time(args)
    if not dates:
        await reply(message, "Please enter a valid time. Examples: `tomorrow`, `10h`, `3 days`")
        return
    seconds = dates[0]
    if seconds < 1 or seconds >= 31536000:
        await reply(message, "Please enter a valid time. Examples: `tomorrow`, `10h`, `3 days`")
        return
    reminder = {
        "timestamp": round(time.time()) + seconds,
        "called_timestamp": round(time.time()),
        "text": dates[1],
        "user_id": message.author.id,
        "channel_id": message.channel.id,
        "message_id": message.id,
        "guild_id": "@me",
        "id": message.id
    }
    if dates[1] == "":
        reminder["text"] = "(No reminder text.)"
    if message.guild:
        reminder["guild_id"] = message.guild.id
    database.add_reminder(reminder)

    current_reminders[message.id] = bot.loop.create_task(tasks.check_reminder(message.id))

    if dates[1] == "":
        await reply(message, f"I'll mention you <t:{time.time() + seconds}:R>.")
    else:
        await reply(message, f"<t:{math.floor(time.time() + seconds)}:R>: {dates[1]}")

@command()
async def reminders(bot, message, **kwargs):
    reminders = 0
    em = discord.Embed(title='Your reminders:')
    for key,reminder in database.fetch_reminders().items():
        if reminder["user_id"] == message.author.id:
            reminders += 1
            em.add_field(name=f"{key}: <t:{math.floor(reminder['timestamp'])}:R>", value=f"[{reminder['text']}](https://discordapp.com/channels/{str(reminder['guild_id'])}/{str(reminder['channel_id'])}/{str(reminder['message_id'])})",inline=False)
    if reminders == 0:
        await reply(message, "You have no reminders.")
        return
    em.set_footer(text="You can cancel a reminder using m!cancelreminder <reminder id>")
    await reply(message, embed=em)

@command()
async def cancelreminder(bot, message, **kwargs):
    try:
        id = int(kwargs["arguments"][0])
    except ValueError:
        await reply(message, "Invalid reminder ID.")
        return
    reminders = database.fetch_reminders()
    if id in reminders:
        if reminders[id]["user_id"] == message.author.id:
            database.remove_reminder(id)
            current_reminders[id].cancel()
            current_reminders.pop(id)
            await reply(message, "Canceled reminder.")
        else:
            await reply(message, "Invalid reminder ID.")
    else:
        await reply(message, "Invalid reminder ID.")
        return
