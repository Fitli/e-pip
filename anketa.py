import re

# I am trying, but I have no idea how to recognize all emojis (both classic and custom) in a message.
# If somebody knows, please tel me!!
async def anketa_cmd(ctx):
    print(ctx.message.content)
    #emotes = re.findall("/<a?:.+?:\d{18}>|\p{Extended_Pictographic}/gu", ctx.message.content)
    emotes = re.findall(r'/<a?:.+?:\d*>', ctx.message.content)
    print(emotes)

# Simple yes/no vote
async def vote_cmd(ctx):
    await ctx.message.add_reaction(emoji='👍')
    await ctx.message.add_reaction(emoji='👎')
