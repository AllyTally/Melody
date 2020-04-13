from aiohttp import ClientSession
import config

commands = {}

def command(auth=None, aliases=None):
    def inner(func):
        name = func.__name__.lstrip('_')
        commands[name] = [func, auth, aliases]
    return inner

def is_botowner(message):
    return message.author.id in config.config["owners"]

async def send(message, text=None, embed=None):
    await message.channel.send(text, embed=embed)

async def fetch(url, agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'):
    async with ClientSession(headers={'User-Agent': agent}) as session:
        async with session.get(url) as response:
            return await response.read()
