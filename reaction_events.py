import discord
from common import command, reply, is_moderator
from client import bot
import time
import tasks
import logs
import database
import utils
import mutes
import emojis
import re

@command(auth=is_moderator)
async def addreactionrole(bot, message, **kwargs):
    args = kwargs["arguments"]

    if len(args) < 3:
        await reply(message, ":x: Invalid amout of arguments passed.")
        return

    emoji = args.pop(0)
    role = args.pop(0)
    message_link = args.pop(0)

    is_custom = False
    emoji_unicode = ""
    emoji_id = 0
    emoji_object = None
    failed_to_get_emoji = False

    if emojis.db.get_emoji_by_code(emoji):
        is_custom = False
        emoji_unicode = emoji
    else:
        emoji_match = re.search("<a?:.*:([0-9]+)>", emoji)
        if emoji_match:
            is_custom = True
            emoji_id = int(emoji_match.group(1))
            emoji_object = bot.get_emoji(emoji_id)
            if not emoji_object:
                failed_to_get_emoji = True
        else:
            await reply(message, ":x: Please enter a valid emoji.")
            return

    role_object = utils.match_input(message.guild.roles, discord.Role, role)

    if not role_object:
        await reply(message, ":x: Please enter a valid role.")
        return
    if role_object.name == "@everyone":
        await reply(message, ":x: You cannot use the `everyone` role.")
        return

    channel_match = re.search("https?://(?:ptb\.|canary\.)?discord\.com/channels/([0-9]+)/([0-9]+)/([0-9]+)", message_link)
    if channel_match:
        guild_id   = int(channel_match.group(1))
        channel_id = int(channel_match.group(2))
        message_id = int(channel_match.group(3))
    else:
        await reply(message, ":x: Please enter a valid message link.")
        return

    if guild_id != message.guild.id:
        await reply(message, ":x: You cannot add reaction roles for other servers.")
        return

    reaction_event = {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "message_id": message_id,
        "custom_emoji": is_custom,
        "role_id": role_object.id,
        "type": "role"
    }

    if is_custom:
        reaction_event["emoji_id"] = emoji_id
    else:
        reaction_event["emoji_unicode"] = emoji_unicode


    database.add_reaction_event(reaction_event)

    channel = await bot.fetch_channel(channel_id)
    if channel:
        targeted_message = await channel.fetch_message(message_id)
        if targeted_message:
            if is_custom:
                if not failed_to_get_emoji:
                    await targeted_message.add_reaction(emoji_object)
            else:
                await targeted_message.add_reaction(emoji_unicode)
        else:
            await reply(message, ":x: Please enter a valid message link.")
            return
    else:
        await reply(message, ":x: Please enter a valid message link.")

    if failed_to_get_emoji:
        await reply(message, "The reaction role was added, but I was unable to add the reaction to the message, most likely because I am not on the server the emote is from. Please react to the message with the custom emoji you input.")
    else:
        await reply(message, "Reaction role added.")

@command(auth=is_moderator)
async def removereactionrole(bot, message, **kwargs):
    args = kwargs["arguments"]

    if len(args) < 2:
        await reply(message, ":x: Invalid amout of arguments passed.")
        return

    message_id = args.pop(0)
    role_or_emoji = args.pop(0)

    try:
        message_id = int(message_id)
    except:
        await reply(message, ":x: Please enter a valid message id.")
        return

    is_custom = False
    emoji_unicode = ""
    emoji_id = 0
    is_role = True

    role_object = utils.match_input(message.guild.roles, discord.Role, role_or_emoji)

    if not role_object:
        is_role = False
        if emojis.db.get_emoji_by_code(emoji):
            is_custom = False
            emoji_unicode = role_or_emoji
        else:
            emoji_match = re.search("<a?:.*:([0-9]+)>", emoji)
            if emoji_match:
                is_custom = True
                emoji_id = int(emoji_match.group(1))
            else:
                await reply(message, ":x: Please enter a valid role or emoji.")
                return

    if is_role:
        if database.remove_reaction_role_by_role_id(role_object.id, message_id).deleted_count != 0:
            await reply(message, f"I have removed the reaction role.")
        else:
            await reply(message, f"The reaction role was not found.")
        return
    else:
        if not is_custom:
            if database.remove_reaction_role_by_unicode(emoji_unicode, message_id).deleted_count != 0:
                await reply(message, f"I have removed the reaction role.")
            else:
                await reply(message, f"The reaction role was not found.")
            return
        else:
            if database.remove_reaction_role_by_id(emoji_id, message_id).deleted_count != 0:
                await reply(message, f"I have removed the reaction role.")
            else:
                await reply(message, f"The reaction role was not found.")

