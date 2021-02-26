from common import command, send, reply, is_botowner
import os
import sys
import config
import inspect
import time
import database
import utils

@command()
async def hello(bot, message, **kwargs):
    await reply(message, ":wave:")

@command()
async def addprefix(bot, message, **kwargs):
    if not kwargs["string_arguments"]:
        await reply(message, ":question:")
        return
    if kwargs["string_arguments"] in database.fetch_global_prefixes():
        await reply(message, ":x: Global prefix already exists!")
        return
    database.add_global_prefix(kwargs["string_arguments"])
    await reply(message, ":thumbsup:")

@command()
async def removeprefix(bot, message, **kwargs):
    if not kwargs["string_arguments"]:
        await reply(message, ":question:")
        return
    if kwargs["string_arguments"] not in database.fetch_global_prefixes():
        await reply(message, ":x: Global prefix doesn't exist!")
        return
    database.remove_global_prefix(kwargs["string_arguments"])
    await reply(message, ":thumbsup:")

@command(auth=is_botowner)
async def _traceback(client, message, **kwargs):
    if errorarray != []:
        await reply(message, "Most recent traceback:\n"+ errorarray[-1])
    else:
        await reply(message, "No recent errors.")

@command(auth=is_botowner)
async def _eval(bot, message, **kwargs):
    """Evaluates code."""
    code = kwargs["string_arguments"]
    if not code == None:
        code = code.strip('` ')
    else:
        await reply(message, "Successfully evaluated nothing.")
        return
    python = '```py\n{}\n```'
    result = None
    env = {
        'message': message,
        'guild': message.guild,
        'channel': message.channel,
        'author': message.author
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
        await reply(message, python.format(type(e).__name__ + ': ' + str(e)))
        return

    await reply(message, python.format(result).replace(config.config["token"],"[TOKEN]")) # TODO: This is ugly and unsafe

@command(auth=is_botowner)
async def kill(bot, message, **kwargs):
    try:
        await reply(message, ":wave:")
    except:
        pass
    database.close()
    await bot.close()

@command(auth=is_botowner)
async def restart(bot, message, **kwargs):
    try:
        msg = await reply(message, "Restarting...")
        info = {
            "restart_channel":  msg.channel.id,
            "restart_message": msg.id,
            "restart_timestamp": time.time()
        }
        database.add_restarted_info(info)
    except:
        pass
    database.close()
    await bot.close()
    os.execv(sys.executable, ['python3', "-u", "/home/ally/melody/bot.py"] + sys.argv[:1])

@command(auth=is_botowner)
async def clean(bot, message, **kwargs):
    async for m in message.channel.history(before=message, limit=25):
        if m.author.id==bot.user.id:
            await m.delete()
