import discord
import asyncio
from common import cleantext, send
import time
import natural.date
import random
from client import bot
import logs
import database

async def random_game():
    ''' Changes the game in the bot's status. '''
    while True:
        gamelist = [
            "[playing] with hearts </3",
            "[playing] on {} servers!".format(len(bot.guilds)),
            "[streaming] on Twitch",
            "[listening] voices...",
            "[watching] you.",
        ]
        picked = random.choice(gamelist)
        name = picked.split("] ")[1]
        type = picked.split("] ")[0].replace("[", "", 1)
        games = {"playing":discord.ActivityType.playing,"streaming":discord.ActivityType.streaming,"listening":discord.ActivityType.listening,"watching":discord.ActivityType.watching}
        game = discord.Activity(name=name + " | Melody", url="https://www.twitch.tv/logout.html", type=games[type])
        await bot.change_presence(activity=game)
        await asyncio.sleep(300)

async def check_reminder(reminder_id):
    current_reminder = database.fetch_reminders()[reminder_id]                 # Store the current reminder
    logs.info("Reminder: Sleeping for " + str(current_reminder["timestamp"] - time.time()))
    await asyncio.sleep(current_reminder["timestamp"] - time.time())           # Sleep until it's time to remind the user
    logs.info("Reminder: Sleep finished.")

    try:
        channel = await bot.fetch_channel(current_reminder["channel_id"])      # Grab the reminder's channel
        readable_time = natural.date.duration(current_reminder["called_timestamp"],precision=3) # Get the time in a readable format
        
        # And finally, send the reminder.
        logs.info("Reminder: Sending reminder")
        await channel.send(content=f"<@{current_reminder['user_id']}>, {readable_time}: {cleantext(current_reminder['text'])}\n\nhttps://discordapp.com/channels/{str(current_reminder['guild_id'])}/{str(current_reminder['channel_id'])}/{str(current_reminder['message_id'])}")

    except:
        return                                                                 # It should be handled next time the bot starts
        logs.warn("Reminder: Couldn't send reminder!")                         # We couldn't send the reminder, so return early

    logs.info("Reminder: Removing reminder")
    database.remove_reminder(reminder_id)                                      # Remove the reminder from the reminders list





async def check_timed_mutes(mute_id):
    logs.info("Mute: Fetching mute")
    current_mute = database.fetch_timed_mutes()[mute_id]                # Store the current mute
    logs.info("Mute: Sleeping for " + str(current_mute["timestamp"] - time.time()))
    await asyncio.sleep(current_mute["timestamp"] - time.time())        # Sleep until it's time to remind the user
    logs.info("Mute: Sleep finished.")

    try:
        guild = await bot.fetch_guild(current_mute["guild_id"])         # Grab the mute's guild

        # And finally, send the reminder.
        logs.info("Mute: Removing muted role")

        member = await guild.fetch_member(current_mute["user_id"])

        role = guild.get_role(current_mute["role_id"])

        await member.remove_roles(role, reason=f"({current_mute['mod_tag']}) Time's up.")


    except:
        return                                                          # It should be handled next time the bot starts
        logs.warn("Mutes: Couldn't unmute user!")                       # We couldn't unmute the user, so return early

    logs.info("Mutes: Removing mute")
    database.remove_timed_mute(member.id)                               # Remove the mute from the mutes list
