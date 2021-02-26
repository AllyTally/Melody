import discord
from common import command, fetch, send, reply
import urllib
import database
import utils
import pytz
import datetime

@command()
async def calc(bot, message, **kwargs):
    if kwargs["string_arguments"] == None:
        await reply(message, "Please enter a math equation.")
        return
    url = "https://api.mathjs.org/v4/?expr=" + urllib.parse.quote(kwargs["string_arguments"])
    data = await fetch(url)
    await reply(message, data.decode())

@command()
async def setpronouns(bot, message, **kwargs):
    if len(kwargs["arguments"]) < 5:
        await reply(message, "To set your pronouns, please enter your preferred pronouns after the command, plus if they're plural pronouns or not (ex. she **is** and they **are**).\n\nExample: `m!setpronouns they them their theirs plural`\n(This system is temporary, it's bad I know)")
        return

    plural = kwargs["arguments"][4].lower() in ["true", "yes", "on", "plural"]

    pronouns = {
        "subject": kwargs["arguments"][0],
        "object": kwargs["arguments"][1],
        "pos_determiner": kwargs["arguments"][2],
        "pos_pronoun": kwargs["arguments"][3],
        "plural": plural
    }

    database.set_pronouns(message.author.id, pronouns)
    string = "Your pronouns have been updated.\n\n"

    is_or_are = "is"
    if plural:
        is_or_are = "are"

    string += f"{message.author.name} went to the store.\n"
    string += f"**{kwargs['arguments'][0].title()}** forgot to bring **{kwargs['arguments'][2]}** wallet with **{kwargs['arguments'][1]}**.\n"
    string += f"**{kwargs['arguments'][0].title()} {is_or_are}** the owner of the wallet.\n"
    string += f"The wallet is **{kwargs['arguments'][3]}**."

    await reply(message, string)

@command()
async def pronouns(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    if args == "":
        args = None
    member = utils.match_input(message.guild.members, discord.Member, args)
    if not member:
        member = message.author
    self = message.author.id == member.id
    if (not utils.has_pronouns(member.id)):
        if self:
            await reply(message, ":x: You have not set up your pronouns. You can do so using `setpronouns`.")
        else:
            await reply(message, ":x: They have not set up a timezone. They can do so using `setpronouns`.")
        return

    user_pronouns = utils.get_user_pronouns(member.id)

    if self:
        await reply(message, f"Your pronouns are `{user_pronouns['subject']}/{user_pronouns['object']}/{user_pronouns['pos_determiner']}/{user_pronouns['pos_pronoun']}`.")
    else:
        await reply(message, f"{user_pronouns['pos_determiner'].title()} pronouns are `{user_pronouns['subject']}/{user_pronouns['object']}/{user_pronouns['pos_determiner']}/{user_pronouns['pos_pronoun']}`.")



@command()
async def timezone(bot, message, **kwargs):
    if not kwargs["string_arguments"]:
        # They want their own timezone!
        user_data = database.fetch_user(message.author.id)
        if (not user_data) or (not user_data.get("timezone")):
            await reply(message, ":x: You have not set up a timezone. You can do so using the `timezone` command.")
        else:
            await reply(message, f"Your timezone is currently set to `{user_data['timezone']}`.")
        return
    if not kwargs["string_arguments"] in pytz.all_timezones:
        await reply(message, ":x: Please enter a valid timezone. Examples: `UTC`, `America/Halifax`, `CET`\n\nA list of valid timezones can be found at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
        return
    database.set_timezone(message.author.id, kwargs["string_arguments"])
    await reply(message, "Your timezone has been updated.")
    # A valid timezone was entered

@command()
async def tf(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    if args == "":
        args = None
    member = utils.match_input(message.guild.members, discord.Member, args)
    if not member:
        member = message.author
    self = message.author.id == member.id
    user_data = database.fetch_user(member.id)
    if (not user_data) or (not user_data.get("timezone")):
        if self:
            await reply(message, ":x: You have not set up a timezone. You can do so using the `timezone` command.")
        else:
            await reply(message, ":x: They have not set up a timezone. They can do so using the `timezone` command.")
        return

    tz = pytz.timezone(user_data["timezone"])
    current_time = datetime.datetime.now(tz)
    string_time = current_time.strftime("%I:%M %p, %Y-%m-%d")
    if self:
        await reply(message, "Your current time is `" + string_time + "`.")
    else:
        await reply(message, "Their current time is `" + string_time + "`.")
