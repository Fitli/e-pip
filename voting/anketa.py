import re
import emoji

async def anketa_cmd(ctx):
    pattern = r'<a?:.+?:\d+?>'

    classic_emotes = emoji.distinct_emoji_list(ctx.message.content)
    if classic_emotes:
        pattern += "|" + "|".join(sorted(classic_emotes, key=lambda x: -len(x)))

    emotes = re.findall(pattern, ctx.message.content)
    for emote in emotes:
        await ctx.message.add_reaction(emote)


# Simple yes/no vote
async def vote_cmd(ctx):
    await ctx.message.add_reaction('👍')
    await ctx.message.add_reaction('👎')
