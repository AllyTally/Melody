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
import inspect
import urllib.parse
import re

bot = discord.Client(status=discord.Status.dnd, activity=discord.Game(name="Starting..."))
errorarray = []
config = {}

def read_config():
    global config
    with open("config.json") as file:
        file_contents = file.read()
        config = json.loads(file_contents)
    required_values = ["token","owners"]
    default_values = {"invokers": ["!"]}
    failed = False
    for item in required_values:
        if not item in config:
            print(item + " is missing from config.json.")
            failed = True
    if failed:
        sys.exit()
    for key, value in default_values.items():
        if not key in config:
            print(key + " is missing from config.json. The default value(s) will be used.")
            config[key] = value
            
read_config()

async def send(message, text=None, embed=None):
    await message.channel.send(text, embed=embed)

async def fetch(url, agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'):
    async with ClientSession(headers={'User-Agent': agent}) as session:
        async with session.get(url) as response:
            return await response.read()

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

commands = {}

def command(auth=None, aliases=None):
    def inner(func):
        name = func.__name__.lstrip('_')
        commands[name] = [func, auth, aliases]
    return inner

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
    global commanda
    global clean_command
    for i in config["invokers"]:
        if message.content.startswith(i):
            commanda = message.content.split(i, 1)[1]
            try:
                clean_command = message.clean_content.split(i, 1)[1]
            except IndexError:
                clean_command = commanda
            invoker = i
            break
    else:
        return # this can be on message triggers if wanted
    try:
        arguments = commanda.split(' ', 1)[1]
        clean_arguments = clean_command.split(' ', 1)[1]
    except IndexError:
        arguments = None
        clean_arguments = None
    command = commanda.split(' ', 1)[0]
    if command in commands:
        func = commands[command]
    else:
        # check if it's an alias
        for c, p in commands.items():
            if p[2] != None and command in p[2]:
                func = commands[c]
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
    kwargs = {'arguments': arguments} # place variables to pass around here. an example would be: kwargs = {'command': command}
    # you don't have to do this, but it's better than globalling variables
    await func[0](bot, message, **kwargs)

def manage_messages(message):
    if message.guild == None:
        return True
    return message.author.guild_permissions.manage_messages

def is_botowner(message):
    return message.author.id == 155651120344203265

@command()
async def hello(bot, message, **kwargs):
    await send(message, ":wave:")

@command(aliases=['internal','intdef','intdefine','internaldefine','internaldef', 'int.scr', 'int.sc', 'intscr', 'intsc'])
async def _int(bot, message, **kwargs):
    if kwargs['arguments'] == None:
        await send(message, "Please enter a command name.")
        return
    keyword = kwargs['arguments']
    data = await fetch("https://tolp.nl/v_intcom/api/v1/json/?command=" + urllib.parse.quote(keyword))
    jsonl = json.loads(data)
    try:
        try:
            thing = jsonl["error"]
        except KeyError:
            thing = None		
        if thing:
            await send(message, jsonl["error"]["message"])
            return
        if jsonl["color"] == "t" or jsonl["color"] == "w":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.lighter_grey())
        elif jsonl["color"] == "b":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.dark_blue())
        elif jsonl["color"] == "o":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.orange())
        elif jsonl["color"] == "r":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.red())
        else:
            em = discord.Embed(title='VVVVVV',colour=discord.Color.lighter_grey())
        tempstring = "{}({})"
        if not jsonl["brackets"]:
            tempstring = "{}"
        em.add_field(name="Description:", value=jsonl["description"])
        em.add_field(name="Usage:", value=tempstring.format(jsonl["name"],str(','.join(map(str, [x["name"] for x in jsonl["args"]])))))
        if jsonl["args"] != []:
            temparray = []
            for i in jsonl["args"]:
                if i["type"] == "T":
                    type = "Text"
                elif i["type"] == "t":
                    type = "Optional text"
                elif i["type"] == "N":
                    type = "Number"
                elif i["type"] == "n":
                    type = "Optional number"
                else:
                    type = "Unknown"
                temparray.append("{} - {} ({})".format(i["name"], i["description"], type))
            em.add_field(name="Arguments:", value=str('\n'.join(map(str, temparray))))
        extra = None
        if jsonl["name"] == "gamestate":
            extra = "[Gamestate list](https://glaceon.ca/V/lists/#glist)"
        elif jsonl["name"] == "createentity":
            extra = "[Entity list](https://glaceon.ca/V/lists/#celist)"
        if extra:
            em.add_field(name="Extra information:", value=extra)
        await send(message, embed=em)
    except IndexError:
        await send(message, "No results.")
    except discord.errors.HTTPException:
        await send(message, "Response too large!")

async def dovtext(passedargs,scr):
    colors = {
        "gray":(174,174,174),
        "grey":(174,174,174),
        "cyan":(164,164,255),
        "viridian":(164,164,255),
        "red":(255,60,60),
        "vermilion":(255,60,60),
        "green":(144,255,144),
        "verdigris":(144,255,144),
        "yellow":(229,229,120),
        "vitellary":(229,229,120),
        "blue":(95,95,255),
        "victoria":(95,95,255),
        "pink":(255,134,255),
        "purple":(255,134,255),
        "violet":(255,134,255),
        "orange":(255,130,20),
        "darkaquamarine": (19,174,174),
        "darkgreen": (19,60,60),
        "brightgreen": (19,255,144),
        "brightblue": (19,95,255),
        "aquamarine": (19,164,255),
        "lessbrightgreen": (19,255,134),
        "brightgreen2": (19,255,134),
        "brighterblue": (19,134,255)
    }
    if scr:
        colors.pop("orange")
    c2 = colors["gray"]
    inputtext=""
    tcol = "gray"
    if passedargs != None:
        args = passedargs.split(" ")
        if args[0].lower() in colors:
            tcol = args[0].lower()
            c2 = colors[args[0].lower()]
            inputtext = " ".join(map(str,args[1:]))
        elif re.match("^(#)?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", args[0]):
            if not scr:
                thingo = args[0].lstrip('#')
                lv = len(thingo)
                c2 = tuple(int(thingo[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
                args.pop(0)
                inputtext = " ".join(map(str,args))
            else:
                c2 = colors["gray"]
                inputtext=passedargs
        else:
            c2 = colors["gray"]
            inputtext=passedargs
    c1 = (math.floor(c2[0]/6),math.floor(c2[1]/6),math.floor(c2[2]/6))
    font = ImageFont.truetype("PetMe64.ttf", 8)
    im = Image.new("RGBA", (1,1), color=c1)
    draw = ImageDraw.Draw(im)
    w,h = draw.multiline_textsize(inputtext, font=font,spacing=2)
    im = im.resize((w+15,h+17))
    draw = ImageDraw.Draw(im)
    draw.multiline_text((7,8), inputtext,c2,font=font,spacing=2)
    draw.rectangle([(1,1),(w+13,h+15)], fill=None, outline=c2)
    draw.rectangle([(2,2),(w+12,h+14)], fill=None, outline=c2)
    draw.rectangle([(4,4),(w+10,h+12)], fill=None, outline=c2)
    temp = BytesIO()
    im.save(temp, format="png")
    temp.flush()
    temp.seek(0)
    dfile = discord.File(temp, filename='output.png')
    if not scr:
        return dfile
    else:
        lines = len(inputtext.split("\n"))
        colorconv = {
            "gray":"gray",
            "grey":"gray",
            "cyan":"cyan",
            "viridian":"cyan",
            "red":"red",
            "vermilion":"red",
            "green":"green",
            "verdigris":"green",
            "yellow":"yellow",
            "vitellary":"yellow",
            "blue":"blue",
            "victoria":"blue",
            "pink":"purple",
            "purple":"purple",
            "violet":"purple",
            "darkaquamarine": "gray",
            "darkgreen": "red",
            "brightgreen": "green",
            "brightblue": "blue",
            "aquamarine": "cyan",
            "lessbrightgreen": "yellow",
            "brightgreen2": "yellow",
            "brighterblue": "purple"
        }
        if tcol in ["darkaquamarine","darkgreen","brightgreen","brightblue","aquamarine","lessbrightgreen","brightgreen2","brighterblue"]:
            tcol = colorconv[tcol]
            t = """squeak({})
text({},0,0,{})
{}
createcrewman(-50,0,blue,0,faceleft)
speak_active""".format(tcol,tcol,lines,inputtext.replace("```",""))
        else:
            tcol = colorconv[tcol]
            t = """squeak({})
text({},0,0,{})
{}
speak_active""".format(tcol,tcol,lines,inputtext.replace("```",""))
        return (dfile,t)

@command()
async def vtext(client, message, **kwargs):
    dfile = await dovtext(kwargs["arguments"],False)
    await message.channel.send(file=dfile)

@command()
async def vtscr(client, message, **kwargs):
    dfile,t = await dovtext(kwargs["arguments"],True)
    await message.channel.send(f"```{t}```",file=dfile)

@command(auth=is_botowner)
async def clean(bot, message, **kwargs):
    async for m in message.channel.history(before=message, limit=25):
        if m.author.id==bot.user.id:
            await m.delete()


@command(auth=is_botowner)
async def _traceback(client, message, **kwargs):
    if errorarray != []:
        await send(message, "Most recent traceback:\n"+ errorarray[-1])
    else:
        await send(message, "No recent errors.")

@command(auth=is_botowner)
async def _eval(bot, message, **kwargs):
    """Evaluates code."""
    code = kwargs["arguments"]
    if not code == None:
        code = code.strip('` ')
    else:
        await send(message, "Successfully evaluated nothing.")
        return
    python = '```py\n{}\n```'
    result = None
    env = {
        'message': message,
        'guild': message.guild,
        'channel': message.channel,
        'author': message.author,
        'match_input': match_input
        }

    env.update(globals())

    try:
        result = eval(code, env)
        if inspect.isawaitable(result):
            result = await result
        try:
            await message.add_reaction('\u2705')
        except:
            pass
    except Exception as e:
        await send(message, python.format(type(e).__name__ + ': ' + str(e)))
        return

    await send(message, python.format(result).replace(config["token"],"[TOKEN]")) # TODO: This is ugly and unsafe

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

@command(auth=is_botowner)
async def kill(bot, message, **kwargs):
    await send(message, ":wave:")
    await bot.logout()

@command(auth=is_botowner)
async def restart(bot, message, **kwargs):
    await bot.close()
    os.execv(sys.executable, ['python3', "-u", "/home/ally/Melody/bot.py"] + sys.argv[:1])

print("Connecting to Discord...")
bot.run(config["token"])