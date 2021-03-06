from aiohttp import ClientSession
import config
import re

commands = {}

def command(auth=None, aliases=None):
    def inner(func):
        name = func.__name__.lstrip('_')
        commands[name] = [func, auth, aliases]
    return inner

def is_botowner(message):
    return message.author.id in config.config["owners"]

def is_moderator(message):
    if not hasattr(message, "guild"):
        return True
    return message.author.guild_permissions.manage_messages

def cleantext(message):
    if not message:
        return None
    message = re.sub(r"(http://|https://)?(?:discord(?:(?:.|.?dot.?)"
                     r"(?:gg|me|li|to|link)|app(?:.|.?dot.?)"
                     r"com\/invite)|(invite|disco)(?:.|.?dot.?)gg)\/"
                     r"[\da-z]+",r"[INVITE REDACTED]",
                      str(message),
                      flags=re.I|re.M
                    )
    message = message.replace("@everyone","[@\u200beveryone]")
    message = message.replace("@here","[@\u200bhere]")
    return message

async def send(message, text=None, embed=None):
    return await message.channel.send(cleantext(text), embed=embed)

async def reply(message, text=None, embed=None, mention=False):
    return await message.reply(cleantext(text), embed=embed)


async def fetch(url, agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'):
    async with ClientSession(headers={'User-Agent': agent}) as session:
        async with session.get(url) as response:
            return await response.read()
