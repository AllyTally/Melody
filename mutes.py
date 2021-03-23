import discord
from common import command, reply, is_moderator
from client import bot
import utils
import shlex
import find_time
from humanfriendly import format_timespan
import time
import database
import tasks
import logs

current_timed_mutes = {}

def create_all_mutes():
    logs.info("Creating mute tasks.")
    for mute_id in database.fetch_timed_mutes():
        logs.info("Creating " + str(mute_id))
        current_timed_mutes[mute_id] = bot.loop.create_task(tasks.check_timed_mutes(mute_id))
        logs.info("Created " + str(mute_id) + " successfully")

async def mute_user(member,message,reason=None,seconds=None,mod_tag=None):
    muted_role = utils.match_input(member.guild.roles, discord.Role, "Muted")
    if not muted_role:
        return False

    await member.add_roles(muted_role, reason=f"({mod_tag}) {reason}")

    if not seconds:
        return True
    if seconds <= 0:
        return True
    
    mute = {
        "timestamp": round(time.time()) + seconds,
        "called_timestamp": round(time.time()),
        "user_id": member.id,
        "message_id": message.id,
        "guild_id": member.guild.id,
        "id": message.id,
        "role_id": muted_role.id,
        "mod_tag": mod_tag
    }

    database.add_timed_mute(mute)

    current_timed_mutes[message.id] = bot.loop.create_task(tasks.check_timed_mutes(message.id))
    return True


@command(auth=is_moderator)
async def mute(bot, message, **kwargs):
    args = kwargs["arguments"]
    output_time = find_time.find_time(kwargs["string_arguments"],True,True)

    if output_time[0]:
        args = shlex.split(output_time[1])
    elif output_time[1]:
        await reply(message, ":x: Invalid length of time. Mute not given.")
        return

    member = utils.match_input(message.guild.members, discord.Member, args[0])

    if not member:
        await reply(message, ":x: Couldn't find user!")
        return

    old_mute = database.fetch_timed_mute(member.id)
    if old_mute:
        if output_time[0]:
            await reply(message, ":x: That member already has a timed mute.")
        else:
            await reply(message, "Raising timed mute to a normal mute. Reason ignored.")
            database.remove_timed_mute(member.id)
            current_timed_mutes[old_mute["id"]].cancel()
            current_timed_mutes.pop(old_mute["id"])
        return

    args.pop(0)
    reason = " ".join(args)
    
    mod_tag = message.author.name + "#" + message.author.discriminator

    worked = await mute_user(member,message,reason,output_time[0],mod_tag)
    if not worked:
        await reply(message, ":x: Mute role not found.")
        return
    
    if output_time[0]:
        readable_time = format_timespan(output_time[0])
        await reply(message, f"User has been muted for {readable_time}.")
    else:
        await reply(message, "User has been muted.")

@command(auth=is_moderator)
async def unmute(bot, message, **kwargs):
    args = kwargs["arguments"]
    member = utils.match_input(message.guild.members, discord.Member, args.pop(0))

    if not member:
        await reply(message, ":x: Couldn't find user!")
        return


    mute = database.fetch_timed_mute(member.id)
    if mute:
        database.remove_timed_mute(member.id)
        current_timed_mutes[mute["id"]].cancel()
        current_timed_mutes.pop(mute["id"])

    muted_role = utils.match_input(member.guild.roles, discord.Role, "Muted")
    if not muted_role:
        await reply(message, ":x: Muted role not found.")
    
    reason = " ".join(args)
    if reason == "":
        reason = None
    mod_tag = message.author.name + "#" + message.author.discriminator
    await member.remove_roles(muted_role, reason=f"({mod_tag}) {reason}")

    await reply(message, "User has been unmuted.")
