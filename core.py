from common import command, is_botowner, send
import os
import sys

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

@command(auth=is_botowner)
async def kill(bot, message, **kwargs):
    await send(message, ":wave:")
    await bot.logout()

@command(auth=is_botowner)
async def restart(bot, message, **kwargs):
    await bot.close()
    os.execv(sys.executable, ['python3', "-u", "/home/ally/Melody/bot.py"] + sys.argv[:1])
