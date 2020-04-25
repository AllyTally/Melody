from common import command, send, is_botowner
import os
import sys
import config
import persistent
import inspect
import time

@command()
async def hello(bot, message, **kwargs):
    await send(message, ":wave:")

@command(auth=is_botowner)
async def _traceback(client, message, **kwargs):
    if errorarray != []:
        await send(message, "Most recent traceback:\n"+ errorarray[-1])
    else:
        await send(message, "No recent errors.")

@command(auth=is_botowner)
async def _eval(bot, message, **kwargs):
    """Evaluates code."""
    code = kwargs["string_arguments"]
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
        await send(message, python.format(type(e).__name__ + ': ' + str(e)))
        return

    await send(message, python.format(result).replace(config.config["token"],"[TOKEN]")) # TODO: This is ugly and unsafe

@command(auth=is_botowner)
async def kill(bot, message, **kwargs):
    try:
        await send(message, ":wave:")
        persistent.persistent["restart_message"] = None
        persistent.persistent["restart_timestamp"] = None
        persistent.save()
    except:
        pass
    await bot.logout()

@command(auth=is_botowner)
async def restart(bot, message, **kwargs):
    try:
        msg = await send(message, "Restarting...")
        persistent.persistent["restart_message"] = [msg.channel.id,msg.id]
        persistent.persistent["restart_timestamp"] = time.time()
        persistent.save()
    except:
        pass
    await bot.close()
    os.execv(sys.executable, ['python3', "-u", "/home/ally/melody/bot.py"] + sys.argv[:1])

@command(auth=is_botowner)
async def clean(bot, message, **kwargs):
    async for m in message.channel.history(before=message, limit=25):
        if m.author.id==bot.user.id:
            await m.delete()
