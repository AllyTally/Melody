import discord
from discord import http
import asyncio
import requests
import sys
import subprocess
import os
import json
import shlex
import random
import traceback
import PIL
from aiohttp import ClientSession
import aiohttp
from PIL import Image, ImageFont, ImageDraw
import math
from io import BytesIO
import urllib.parse
import common
from common import command, send, is_botowner
import config

bot = discord.Client(status=discord.Status.dnd, activity=discord.Game(name="Starting..."))
errorarray = []

async def get_last_attachment(message):
    last_attachment = None
    async for m in message.channel.history(before=message, limit=25):
        if m.attachments:
            last_attachment = m.attachments[0].url
            break
        elif m.embeds:
            last_attachment = m.embeds[0].url
            if not (type(last_attachment) is type(discord.Embed.Empty)):
                break
            last_attachment = m.embeds[0].image.url
            if not (type(last_attachment) is type(discord.Embed.Empty)):
                break
    return last_attachment

def match_input(iterable, objtype, request):
	"""Return a member/guild/channel/role/emoji object given an input which could be anything
	that identifies that object. If it can't be found, return None.

	iterable: The iterable to search through.

	objtype: A discord.py class that specifies the type of object to search for. Can be either
	discord.Member, discord.Guild, discord.abc.GuildChannel, discord.Role, or discord.Emoji.
	Note that this function doesn't actually use isinstance() or do any type-checking with this,
	this just specifies which attributes to check for, kind of like an enum.

	request: A string that will be tried to be matched to.

	It is recommended you filter out unneeded objects from `iterable` when using this function.

	The following priority is used:
	1) (Members only) Mention: <@146814960574398464> or <@!146814960574398464>
	2) (Channels only) Mention: <#153368829160849408>
	3) (Roles only) Mention: <@&153369506813706240>
	4) (Emojis only) Emoji: <:unjoy:263889385492185088>
	5) ID: 146814960574398464
	6) (Members only) Username/Username+Discriminator (Discord tag)/Nickname, whatever
	discord.Guild.get_member_named() accepts: Info Teddy, Info Teddy#3737, info teddy
	7) Name: tOLP, general, Owner, unjoy
	8) (Members only) Case-insensitive nickname complete match: info teddy
	9) Case-insensitive name complete match: Info Teddy, tolp, owner
	10) (Members only) Case-insensitive nickname partial match: info
	11) Case-insensitive name partial match: Info, tOL, own
	12) (Members only) Discriminator only (either with or without #): 3737
	"""
	acceptvals = (
		discord.Member,
		discord.Guild,
		discord.abc.GuildChannel,
		discord.Role,
		discord.Emoji,
	)
	if objtype not in acceptvals:
		raise ValueError('objtype has to be one of ' + str(acceptvals))

	target = None

	# Is this a mention, or an emoji? If so, extract the ID from it
	if request.startswith('<') and request.endswith('>'):
		if (objtype is discord.Member and request[1:3] == '@!') or \
		(objtype is discord.Role and request[1:3] == '@&'):
			request = int(request[3:-1])
		elif (objtype is discord.Member and request[1] == '@') or \
		(objtype is discord.abc.GuildChannel and request[1] == '#'):
			request = int(request[2:-1])
		elif objtype is discord.Emoji and request[1] == request[-20] == ':':
			request = int(request[-19:-1])
	elif request.isdigit() and len(request) != 4:
		request = int(request)

	# Now get the object from the ID (if we got any)
	target = discord.utils.find(lambda x: x.id == request, iterable)

	if target is not None:
		return target

	# We're still executing, so we didn't get an ID
	if objtype is discord.Member:
		# Not my problem
		return match_member_attrs(iterable, request)

	# Every other type here

	namematched = None
	namefound = None

	for obj in iterable:
		if obj.name is None:
			continue
		if obj.name.lower() == request.lower():
			namematched = obj
			break
		if obj.name.lower().find(request.lower()) != -1:
			namefound = obj
			break

	target = namematched if namematched else namefound

	return target

def match_member_attrs(iterable, request):
	"""Return a discord.Member object from an iterable of discord.Member objects, given a
	string that could match the object in any way.

	This is a match_input() helper function.

	The following priority is used:
	1) Username/Username+Discriminator (Discord tag)/Nickname, whatever
	discord.Guild.get_member_named() accepts: Info Teddy, Info Teddy#3737, info teddy
	2) Name: tOLP, general, Owner, unjoy
	3) Case-insensitive nickname complete match: info teddy
	4) Case-insensitive name complete match: Info Teddy, tolp, owner
	5) Case-insensitive nickname partial match: info
	6) Case-insensitive name partial match: Info, tOL, own
	7) Discriminator only (either with or without #): 3737
	"""
	# Let's create an object close to a discord.Guild, so we
	# can use discord.Guild.get_member_named()
	DuckTypedGuild = type('', (), {'members': []})  # Creates a somewhat bare class
	dt_guild = DuckTypedGuild()

	dt_guild.members = iterable

	target = discord.Guild.get_member_named(dt_guild, request)

	if target is not None:
		return target

	# Not found by guild.get_member_named()

	# Everything else fails? Then try searching.
	# Nicknames have priority, then usernames.
	# Maybe we're entering just a discriminator, match those as well.
	nickmatched = None
	usermatched = None
	nickfound = None
	userfound = None
	discmatched = None

	for member in dt_guild.members:
		if member.nick and member.nick.lower() == request.lower():
			nickmatched = member
			break
		if member.name.lower() == request.lower():
			usermatched = member
			break
		if member.nick and member.nick.lower().find(request.lower()) != -1:
			nickfound = member
			break
		if member.name.lower().find(request.lower()) != -1:
			userfound = member
			break
		if member.discriminator == request or \
		(request.startswith('#') and \
		member.discriminator == request[1:]):
			discmatched = member
			break

	target = nickmatched if nickmatched is not None else \
	usermatched if usermatched is not None else \
	nickfound if nickfound is not None else \
	userfound if userfound is not None else \
	discmatched

	return target


def cleantext(message):
    message = re.sub(r"(http://|https://)?(?:discord(?:(?:.|.?dot.?)(?:gg|me|li|to|link)|app(?:.|.?dot.?)com\/invite)|(invite|disco)(?:.|.?dot.?)gg)\/[\da-z]+",r"[INVITE REDACTED]",str(message),flags=re.I|re.M)
    message = message.replace("@everyone","[@\u200beveryone​]")
    message = message.replace("@here","[@\u200bhere]")
    return message

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

import vtext
import v_intcom
import general
import core

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print("Server count: {}".format(len(bot.guilds)))
    bot.loop.create_task(random_game())

@bot.event
async def on_error(event, *args, **kwargs):
    for i in bot.guilds:
        foundowner = discord.utils.get(i.members, id=155651120344203265)
        if foundowner != None:
            break
    if foundowner == None:
        return
    print(traceback.format_exc())
    if type(args[0]) is discord.Message:
        await args[0].channel.send("An unexpected error occured! Oops. Please don't try to cause it a second time!")
        await foundowner.send(f"Traceback: ```py\n{traceback.format_exc()}```\nServer: {args[0].guild}\nChannel: {args[0].channel}\nMessage ID: {args[0].id}\nMessage content: {args[0].content}")
    errorarray.append("```py\n" + traceback.format_exc() + "```")

#@bot.event
#async def on_message_delete(message):
#    snipes[message.channel.id] = message

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    global unsplit_command
    for i in config.config["invokers"]:
        if message.content.startswith(i):
            unsplit_command = message.content.split(i, 1)[1]
            invoker = i
            break
    else:
        return # This isn't a command!
    split_command = list(filter(None, unsplit_command.split(" ")))
    if split_command == []:
        return # They didn't enter anything after the invoker, which is odd...
    command = split_command[0]
    arguments = split_command[1:]
    string_arguments = unsplit_command.split(command, 1)[1].strip() # Some commands might want arguments in string form, to preserve spacing and such
    
    if command in common.commands:
        func = common.commands[command]
    else:
        # Is this an alias?
        for c, p in common.commands.items():
            if p[2] != None and command in p[2]:
                func = common.commands[c]
                break
        else:
            return # it's not an alias, and thus, an invalid command. if you want, you can put code here to signal that the command entered was invalid, instead of just a return
    print("{} (#{}): {}: {}".format(message.guild, message.channel, message.author.name.encode("ascii","backslashreplace").decode(), message.content.encode("ascii","backslashreplace").decode()))
    if func[1] != None and not func[1](message): # auth check
        if func[1].__name__ == "is_botowner":
            await send(message, "You need to be the bot owner to use this command!")
        elif func[1].__name__ == "manage_messages":
            await send(message, "You need the **manage messages** permission to use this command!")
        else:
            await send(message, "You don't have permission to use this command.\nTo find out who can use this, use the **help** command.")
        return # this person does not have permission. again, if you want, you can put code here to signal that the command caller has no permission to do this, instead of just a return
    kwargs = {'arguments': arguments, 'string_arguments': string_arguments} # place variables to pass around here. an example would be: kwargs = {'command': command}
    # you don't have to do this, but it's better than globalling variables
    await func[0](bot, message, **kwargs)

def manage_messages(message):
    if message.guild == None:
        return True
    return message.author.guild_permissions.manage_messages

def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')
def get_syntax_error(e):
    if e.text is None:
        return '```py\n{0.__class__.__name__}: {0}\n```'.format(e)
    return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

config.read_config()

print("Connecting to Discord...")
bot.run(config.config["token"])
