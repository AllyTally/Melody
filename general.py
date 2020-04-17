from common import command, fetch, send
import urllib

@command()
async def calc(bot, message, **kwargs):
    if kwargs["string_arguments"] == None:
        await send(message, "Please enter a math equation.")
        return
    url = "https://api.mathjs.org/v4/?expr=" + urllib.parse.quote(kwargs["string_arguments"])
    data = await fetch(url)
    await send(message, data.decode())
