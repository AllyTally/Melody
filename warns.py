import discord
from common import command, reply, is_moderator
from client import bot
import find_time
from humanfriendly import format_timespan
import time
import tasks
import find_time
import logs
import database
import utils

@command()
async def warnings(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    if args == "":
        args = None
    member = utils.match_input(message.guild.members, discord.Member, args)
    if not member:
        member = message.author
    self = message.author.id == member.id

    user_pronouns = utils.get_user_pronouns(member.id)
    if self:
        user_pronouns = utils.get_user_pronouns(None)


    has_or_have = "has"
    if user_pronouns["plural"]:
        has_or_have = "have"


    warnings = database.fetch_warnings(member.id, message.guild.id)
    if len(warnings) == 0:
        await reply(message, f":x: {user_pronouns['subject'].title()} {has_or_have} no warnings in **{message.guild.name}**.")
        return

    total_points = 0
    for warning in warnings:
        total_points += warning['points']
    
    points = "points"
    if total_points == 1:
        points = "point"

    description = f"{user_pronouns['subject'].title()} {has_or_have} **{total_points}** warning {points}, and {user_pronouns['subject']} {has_or_have} been warned **{len(warnings)}** times.\n"
    for warning in warnings:
        points = "points"
        if warning['points'] == 1:
            points = "point"
        description += f" - **{warning['id']}**: `{str(warning['mod_tag'])} | {str(warning['points'])} {points}` {warning['reason']}\n"
    
    embed = discord.Embed(title=f'{user_pronouns["pos_determiner"].title()} warnings:', description=description)
    await reply(message, embed=embed)

@command(auth=is_moderator)
async def warn(bot, message, **kwargs):
    points = 1
    args = kwargs["arguments"]
    for index, string in enumerate(args):
        if string in ["-p", "--points"]:
            try:
                points = int(args[index + 1])
            except IndexError:
                await reply(message, ":x: Missing amount of points. No warning given.")
                return            
            except ValueError:
                await reply(message, ":x: Invalid amount of points. No warning given.")
                return
            if points < 0:
                await reply(message, ":x: Invalid amount of points. No warning given.")
                return
            args.pop(index + 1)
            args.pop(index)

    member = utils.match_input(message.guild.members, discord.Member, args[0])

    if not member:
        await reply(message, ":x: Couldn't find user!")
        return

    args.pop(0)
    reason = " ".join(args)

    warning = {
        "user_id": member.id,
        "id": database.new_id(),
        "guild_id": message.guild.id,
        "points": points,
        "reason": reason,
        "mod_tag": message.author.name + "#" + message.author.discriminator,
        "mod_id": message.author.id
    }

    database.add_warning(warning)


    message_contents = f"**{member.name}**#{member.discriminator} (`{member.id}`) has been warned"
    if points == 1:
        message_contents += "."
    else:
        message_contents += f" for **{points}** points."
    await reply(message, message_contents)

@command(auth=is_moderator)
async def pardon(bot, message, **kwargs):
    if not kwargs["arguments"]:
        await reply(message, ":x: Please enter a warning id.")
        return
    id = kwargs["arguments"][0]
    try:
        id = int(id)
    except ValueError:
        await reply(message, ":x: Please enter a valid id.")
        return

    warning = database.fetch_warning(id)
    
    if warning["guild_id"] != message.guild.id:
        await reply(message, ":x: That warning didn't happen on this server.")
        return

    points = warning["points"]
    database.remove_warning(id)

    try:
        member = await message.guild.fetch_member(int(warning["user_id"]))
    except:
        await reply(message, ":x: Error getting user. Their warning has been removed.")
        return

    message_contents = f"**{member.name}**#{member.discriminator} (`{member.id}`) has been pardoned"
    if points == 1:
        message_contents += "."
    else:
        message_contents += f" for **{points}** points."
    await reply(message, message_contents)
