# pylint: disable=missing-module-docstring, missing-function-docstring
import traceback
import time
import database
import discord
from client import bot
import common
from common import reply
import config
import tasks
import reminders
import webserver
import logs

# pylint: disable=unused-import
import vtext
import v_intcom
import general
import core
# pylint: enable=unused-import

#bot = discord.Client(status=discord.Status.dnd, activity=discord.Game(name="Starting..."))
errorarray = []

async def get_last_attachment(message):
    last_attachment = None
    async for current_message in message.channel.history(before=message, limit=25):
        if current_message.attachments:
            last_attachment = current_message.attachments[0].url
            break
        if current_message.embeds:
            last_attachment = current_message.embeds[0].url
            if not type(last_attachment) is type(discord.Embed.Empty):
                break
            last_attachment = current_message.embeds[0].image.url
            if not type(last_attachment) is type(discord.Embed.Empty):
                break
    return last_attachment

#pylint: disable=invalid-name, global-statement
first_ready = True

@bot.event
async def on_ready():
    logs.log('Logged in as')
    logs.log(bot.user.name)
    logs.log(bot.user.id)
    logs.log('------')
    logs.log("Server count: {}".format(len(bot.guilds)))
    global first_ready
    if first_ready:
        first_ready = False
#pylint: enable=invalid-name, global-statement

        logs.info("Starting random game task...")
        bot.loop.create_task(tasks.random_game())
        logs.info("Starting reminder tasks...")
        reminders.create_all_reminders()
        logs.info("Starting webserver task...")
        bot.loop.create_task(webserver.start_server())
        logs.info("All tasks started successfully.")

        try:
            restarted_data = database.fetch_restarted_info()
            if restarted_data:
                channel = await bot.fetch_channel(restarted_data["restart_channel"])
                msg = await channel.fetch_message(restarted_data["restart_message"])
                seconds = time.time() - restarted_data["restart_timestamp"]
                await msg.edit(content=f"Bot restarted in {seconds} seconds.")
        except: # pylint: disable=bare-except
            logs.warn("Couldn't send restarted message!")

        database.clear_restarted_info()

@bot.event
async def on_error(event, *args, **kwargs): # pylint: disable=unused-argument
    for i in bot.guilds:
        foundowner = discord.utils.get(i.members, id=155651120344203265)
        if foundowner is not None:
            break
    if foundowner is None:
        return
    logs.error(traceback.format_exc())
    if isinstance(args[0], discord.Message):
        await args[0].reply("An unexpected error occured! Please avoid causing it again.")
        await foundowner.send(f"Traceback: ```py\n{traceback.format_exc()}```\nServer: "
                               "{args[0].guild}\nChannel: {args[0].channel}\nMessage ID: "
                               "{args[0].id}\nMessage content: {args[0].content}"
                             )
    errorarray.append("```py\n" + traceback.format_exc() + "```")

#@bot.event
#async def on_message_delete(message):
#    snipes[message.channel.id] = message

@bot.event
async def on_message(message): # pylint: disable=too-many-branches
    if message.author == bot.user or message.author.bot:
        return
    unsplit_command = None
    #for i in config.config["invokers"]:
    for i in database.fetch_global_prefixes():
        if message.content.startswith(i):
            unsplit_command = message.content.split(i, 1)[1]
            #invoker = i
            break
    else:
        return # This isn't a command!
    split_command = list(filter(None, unsplit_command.split(" ")))
    if split_command == []:
        return # They didn't enter anything after the invoker, which is odd...
    command = split_command[0]
    arguments = split_command[1:]
    # Some commands might want arguments in string form, to preserve spacing and such
    string_arguments = unsplit_command.split(command, 1)[1].strip()

    if command in common.commands:
        func = common.commands[command]
    else:
        # Is this an alias?
        for command_id, current_command in common.commands.items():
            if current_command[2] is not None and command in current_command[2]:
                func = common.commands[command_id]
                break
        else:
            return # This is an invalid command.
    logs.log("{} (#{}): {}: {}"
          .format(
                  message.guild,
                  message.channel,
                  message.author.name.encode("ascii","backslashreplace").decode(),
                  message.content.encode("ascii","backslashreplace").decode()
                 )
         )
    if func[1] is not None and not func[1](message): # auth check
        if func[1].__name__ == "is_botowner":
            await reply(message, "You need to be the bot owner to use this command!")
        elif func[1].__name__ == "manage_messages":
            await reply(message, "You need the **manage messages** permission to use this command!")
        else:
            await reply(message, "You don't have permission to use this command.\n"
                                 "To find out who can use this, use the **help** command.")
        return
    kwargs = {'arguments': arguments, 'string_arguments': string_arguments}
    # place variables to pass around here. an example would be: kwargs = {'command': command}
    # you don't have to do this, but it's better than globalling variables
    await func[0](bot, message, **kwargs)

def manage_messages(message):
    if message.guild is None:
        return True
    return message.author.guild_permissions.manage_messages

def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')
def get_syntax_error(error):
    if error.text is None:
        return '```py\n{0.__class__.__name__}: {0}\n```'.format(error)
    return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(error, '^', type(error).__name__)

config.read_config()
database.connect()

logs.info("Connecting to Discord...")
bot.run(config.config["token"])
