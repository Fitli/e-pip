import json
import discord
import random

client = discord.Client()

with open("emojis.txt") as f:
    emojis = f.read().split(" ")

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

async def mark_random_emoji(message):
    emoji = random.choice(emojis)
    await message.add_reaction(emoji)
    return emoji

@client.event
async def on_message(message):
    mark = mark_random_emoji(message)
    
    if message.author == client.user:
        return
    
    if message.content.startswith('$ahoj'):
        await message.channel.send("Ahoj!")
        
    if message.content.startswith('$mark'):
        messages = await message.channel.history(limit=200).flatten()
        for msg in messages:
            await mark_random_emoji(msg)

    await mark


#@client.event
#async def on_ready():
    #fp = open("stezbot_500.png", 'rb')
    #pfp = fp.read()
    #await client.user.edit(avatar=pfp)
    
#@client.command()
#async def join(ctx):
    #if message.author == client.user:
        #return
    
    #channel = ctx.author.voice.channel
    #await channel.connect()

#@client.command()
#async def leave(ctx):
    #if message.author == client.user:
        #return
    
    #channel = ctx.author.voice.channel
    #if len(channel.members) == 1:
        #await ctx.voice_client.disconnect()


with open("config.json") as f:
    token = json.load(f)["token"]
client.run(token) 
