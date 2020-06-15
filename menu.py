import discord
import asyncio
from client import bot

default_settings = {
    "message_content": None,
    "first_embed": 0,
    "reaction_settings": {
        "type": 0, # 0 for left/right/cancel, 1 for buttons (not implemented yet)
        "reactions": {
            "⬅️": 0,
            "➡️": 1,
            "❌": 2
        }
    }
}

expired = discord.Embed(title="❌ Embed timed out")
closed = discord.Embed(title="❌ Embed closed")

async def safe_remove_reaction(message, emoji, member):
    try:
        await message.remove_reaction(emoji, member)
    except:
       pass

async def listmenu(message, embed_list, settings = default_settings):
    msg = await message.channel.send(settings.get("message_content", None), embed=embed_list[settings.get("first_embed", 0)])
    current_embed = settings["first_embed"]
    for i in list(settings["reaction_settings"]["reactions"].keys()):
        await msg.add_reaction(i)
    def check(reaction, user):
        return user == message.author and str(reaction.emoji) in list(settings["reaction_settings"]["reactions"].keys())
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await msg.edit(embed=expired)
            break
        else:
            if settings["reaction_settings"]["reactions"][str(reaction.emoji)] == 0:
                current_embed -= 1
                if current_embed < 0:
                    current_embed = len(embed_list) - 1
                await safe_remove_reaction(msg,reaction.emoji,user)
            elif settings["reaction_settings"]["reactions"][str(reaction.emoji)] == 1:
                current_embed += 1
                if current_embed >= len(embed_list):
                    current_embed = 0
                await safe_remove_reaction(msg,reaction.emoji,user)
            elif settings["reaction_settings"]["reactions"][str(reaction.emoji)] == 2:
                await msg.edit(embed=closed)
                break
            await msg.edit(embed=embed_list[current_embed])

    return message