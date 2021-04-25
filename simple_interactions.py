import discord.ext.commands


async def reply_on_mention(bot_user: discord.ext.commands.Bot, msg: discord.Message):
    if bot_user in msg.mentions:
        await msg.channel.send("Mluvili jste o mně?")
