import discord
from common import command, fetch, send, reply
import urllib
import find_time
from humanfriendly import format_timespan
import time
import persistent
import tasks

@command()
async def calc(bot, message, **kwargs):
    if kwargs["string_arguments"] == None:
        await reply(message, "Please enter a math equation.")
        return
    url = "https://api.mathjs.org/v4/?expr=" + urllib.parse.quote(kwargs["string_arguments"])
    data = await fetch(url)
    await reply(message, data.decode())
