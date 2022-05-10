import re
import emojis

#
async def anketa_cmd(ctx):
    #custom_emotes = re.findall(r'<a?:.+:\d{18}>', ctx.message.content)
    classic_emotes = list(emojis.get(ctx.message.content))
    emotes = re.findall(r'<a?:.+:\d{18}>|' + "|".join(classic_emotes), ctx.message.content)
    for emote in emotes:
        await ctx.message.add_reaction(emoji=emote)

# Simple yes/no vote
async def vote_cmd(ctx):
    await ctx.message.add_reaction(emoji='👍')
    await ctx.message.add_reaction(emoji='👎')
