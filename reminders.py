import discord
from common import command, reply
import find_time
from humanfriendly import format_timespan
import time
import persistent
import tasks
import find_time

current_reminders = {}

def create_all_reminders():
    print("Creating reminder tasks.")
    for reminder_id in persistent.persistent["reminders"]:
        print("Creating " + str(reminder_id))
        current_reminders[reminder_id] = bot.loop.create_task(tasks.check_reminder(reminder_id))
        print("Created " + str(reminder_id) + " successfully")

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
    readable_time = format_timespan(seconds)
    reminder = {
        "timestamp": round(time.time()) + seconds,
        "called_timestamp": round(time.time()),
        "text": dates[1],
        "user_id": message.author.id,
        "channel_id": message.channel.id,
        "message_id": message.id,
        "guild_id": "@me"
    }
    if dates[1] == "":
        reminder["text"] = "(No reminder text.)"
    if message.guild:
        reminder["guild_id"] = message.guild.id
    persistent.persistent["reminders"][message.id] = reminder

    current_reminders[message.id] = bot.loop.create_task(tasks.check_reminder(message.id))

    if dates[1] == "":
        await reply(message, f"{message.author.mention}, I'll mention you in {readable_time}.")
    else:
        await reply(message, f"{message.author.mention}, in {readable_time}: {dates[1]}")

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
    if id in persistent.persistent["reminders"]:
        if persistent.persistent["reminders"][id]["user_id"] == message.author.id:
            persistent.persistent["reminders"].pop(id)
            current_reminders[id].cancel()
            current_reminders.pop(id)
            await reply(message, "Canceled reminder.")
        else:
            await reply(message, "Invalid reminder ID.")
    else:
        await reply(message, "Invalid reminder ID.")
        return
