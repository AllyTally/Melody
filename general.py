import discord
from common import command, fetch, send, reply
import urllib
import database
import utils
import pytz
import datetime
import json

@command()
async def help(bot, message, **kwargs):
    with open('help.json', encoding='utf8') as json_file:
        help_file = json.load(json_file)

    if not kwargs["arguments"]:
        embed = discord.Embed(description=help_file["header"])
        embed.colour = discord.Colour.from_rgb(255,169,229)
        for category in help_file["categories"].values():
            embed.add_field(name=category["name"] + " Commands", value="```" + ", ".join([x for x in category["commands"]]) + "```")
        embed.add_field(name="\u200B",value=help_file["footer"], inline=False)
        await reply(message, embed=embed)
        return

    for category in help_file["categories"].values():
        if kwargs["string_arguments"] in category["commands"]:
            command = category["commands"][kwargs["string_arguments"]]
            description  = "__**Usage:**__ `"
            description += kwargs["string_arguments"]

            if command.get("usage"):
                description += " " + command["usage"]

            description += "`\n"

            if command.get("example"):
                description += "__**Example usage:**__ `"
                description += kwargs["string_arguments"]
                description += " " + command["example"]
                description += "`\n"

            description += command["description"]
            embed = discord.Embed(title="Command information for " + kwargs["string_arguments"], description=description)
            embed.colour = discord.Colour.from_rgb(255,169,229)
            embed.set_footer(text="Arguments in [square brackets] are optional.")
            await reply(message, embed=embed)
            return

    await reply(message, ":x: Unknown command.")
    return

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
    await message.add_reaction("✅")

    pronouns = {}

    dm_message = await message.author.send("Please enter your **Subject Pronoun**. (he/she/they/etc)\n(Letters only, limit of 5)")

    def check(m):
        return m.author.id == message.author.id and m.channel.id == dm_message.channel.id

    response_message = await bot.wait_for('message', check=check)
    pronouns["subject"] = response_message.content

    if (not response_message.content.isalpha() or len(response_message.content) > 5):
        await message.author.send("Content too long or includes non-letters, cancelled.")
        return

    dm_message = await message.author.send("Please enter your **Object Pronoun**. (him/her/them/etc)\n(Letters only, limit of 5)")
    response_message = await bot.wait_for('message', check=check)
    pronouns["object"] = response_message.content

    if (not response_message.content.isalpha() or len(response_message.content) > 5):
        await message.author.send("Content too long or includes non-letters, cancelled.")
        return

    dm_message = await message.author.send("Please enter your **Possessive Determiner**. (his/her/their/etc)\n(Letters only, limit of 5)")
    response_message = await bot.wait_for('message', check=check)
    pronouns["pos_determiner"] = response_message.content

    if (not response_message.content.isalpha() or len(response_message.content) > 5):
        await message.author.send("Content too long or includes non-letters, cancelled.")
        return

    dm_message = await message.author.send("Please enter your **Possessive Pronoun**. (his/hers/theirs/etc)\n(Letters only, limit of 6)")
    response_message = await bot.wait_for('message', check=check)
    pronouns["pos_pronoun"] = response_message.content

    if (not response_message.content.isalpha() or len(response_message.content) > 6):
        await message.author.send("Content too long or includes non-letters, cancelled.")
        return

    dm_message = await message.author.send(f"Should it be **{pronouns['subject']} is** or **{pronouns['subject']} are**?")

    await dm_message.add_reaction("1️⃣")
    await dm_message.add_reaction("2️⃣")

    def check(reaction, user):
        return user.id == message.author.id and str(reaction.emoji) in ['1️⃣', '2️⃣']

    reaction, user = await bot.wait_for('reaction_add', check=check)

    pronouns["plural"] =  str(reaction.emoji) == "2️⃣"

    is_or_are = "is"
    if pronouns["plural"]:
        is_or_are = "are"

    string = "**Is this correct?**\n\n"
    string += f"{message.author.name} went to the store.\n"
    string += f"**{pronouns['subject'].title()}** forgot to bring **{pronouns['pos_determiner']}** wallet with **{pronouns['object']}**.\n"
    string += f"**{pronouns['subject'].title()} {is_or_are}** the owner of the wallet.\n"
    string += f"The wallet is **{pronouns['pos_pronoun']}**."
    string += "\n\nIs this okay?"
    dm_message = await message.author.send(string)

    await dm_message.add_reaction("✅")
    await dm_message.add_reaction("❌")

    def check(reaction, user):
        return user.id == message.author.id and str(reaction.emoji) in ['✅', '❌']

    reaction, user = await bot.wait_for('reaction_add', check=check)
    if str(reaction.emoji) == "✅":
        database.set_pronouns(message.author.id, pronouns)
        await message.author.send("Your pronouns have been updated.")
    else:
        await message.author.send("Cancelled.")

@command()
async def pronouns(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    member = None

    if args == "":
        args = None

    if message.guild:
        member = utils.match_input(message.guild.members, discord.Member, args)

    if not member:
        member = message.author
    self = message.author.id == member.id
    if (not utils.has_pronouns(member.id)):
        if self:
            await reply(message, ":x: You have not set up your pronouns. You can do so using `setpronouns`.")
        else:
            await reply(message, ":x: They have not set up their pronouns. They can do so using `setpronouns`.")
        return

    user_pronouns = utils.get_user_pronouns(member.id)

    first_word = user_pronouns['pos_determiner'].title()

    if self:
        first_word = "Your"

    await reply(message, f"{first_word} pronouns are `{user_pronouns['subject']}/{user_pronouns['object']}/{user_pronouns['pos_determiner']}/{user_pronouns['pos_pronoun']}`.")



@command()
async def timezone(bot, message, **kwargs):
    if not kwargs["string_arguments"]:
        # They want their own timezone!
        user_data = database.fetch_user(message.author.id)
        if (not user_data) or (not user_data.get("timezone")):
            await reply(message, ":x: You have not set up a timezone. Examples of valid timezones: `UTC`, `America/Halifax`\n\nA list of valid timezones can be found at: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>")
        else:
            await reply(message, f"Your timezone is currently set to `{user_data['timezone']}`.")
        return
    if not kwargs["string_arguments"] in pytz.all_timezones:
        await reply(message, ":x: Please enter a valid timezone. Examples: `UTC`, `America/Halifax`\n\nA list of valid timezones can be found at: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>")
        return
    database.set_timezone(message.author.id, kwargs["string_arguments"])
    await reply(message, "Your timezone has been updated.")
    # A valid timezone was entered

@command()
async def tf(bot, message, **kwargs):
    args = kwargs["string_arguments"]
    if args == "":
        args = None
    member = None
    if message.guild:
        member = utils.match_input(message.guild.members, discord.Member, args)
    if not member:
        member = message.author
    self = message.author.id == member.id
    user_data = database.fetch_user(member.id)
    if (not user_data) or (not user_data.get("timezone")):

        user_pronouns = utils.get_user_pronouns(member.id)

        if self:
            user_pronouns = utils.get_user_pronouns(None)

        has_or_have = "has"
        if user_pronouns["plural"]:
            has_or_have = "have"
        await reply(message, f":x: {user_pronouns['subject'].title()} {has_or_have} not set up a timezone. {user_pronouns['subject'].title()} can do so using the `timezone` command.")
        return

    tz = pytz.timezone(user_data["timezone"])
    current_time = datetime.datetime.now(tz)
    string_time = current_time.strftime("%I:%M %p, %Y-%m-%d")

    user_pronouns = utils.get_user_pronouns(member.id)
    if self:
        user_pronouns = utils.get_user_pronouns(None)

    await reply(message, f"{user_pronouns['pos_determiner'].title()} current time is `" + string_time + "`.")
