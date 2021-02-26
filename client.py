import discord

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True

bot = discord.Client(
    status=discord.Status.dnd,
    activity=discord.Game(name="Starting..."),
    allowed_mentions = discord.AllowedMentions(everyone=False,roles=False,replied_user=False),
    intents = intents
)

