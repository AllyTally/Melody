from common import command, fetch, send, reply
import urllib
import json
import discord

async def handle_int(message,keyword):
    if keyword == None:
        await reply(message, "Please enter a command name.")
        return
    url = "https://tolp.nl/v_intcom/api/v1/json/?command=" + urllib.parse.quote(keyword)
    data = await fetch(url)
    jsonl = json.loads(data)
    try:
        try:
            thing = jsonl["error"]
        except KeyError:
            thing = None
        if thing:
            await reply(message, jsonl["error"]["message"])
            return
        if jsonl["color"] == "t" or jsonl["color"] == "w":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.lighter_grey())
        elif jsonl["color"] == "b":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.dark_blue())
        elif jsonl["color"] == "o":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.orange())
        elif jsonl["color"] == "r":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.red())
        elif jsonl["color"] == "P":
            em = discord.Embed(title='VVVVVV',colour=discord.Color.magenta())
            em.set_footer(text="This command was added by VVVVVV: Community Edition")
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
            extra = "[Gamestate list](https://glaceon.ca/V/gamestates/)"
        elif jsonl["name"] == "createentity":
            extra = "[Entity list](https://glaceon.ca/V/entities/)"
        if extra:
            em.add_field(name="Extra information:", value=extra)
        await reply(message, embed=em)
    except IndexError:
        await reply(message, "No results.")
    except discord.errors.HTTPException:
        await reply(message, "Response too large!")

@command()
async def _int(bot, message, **kwargs):
    await handle_int(message, kwargs["string_arguments"])
