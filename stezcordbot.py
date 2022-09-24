import json
import sys

import discord
from discord.ext import commands, tasks
import random
from vesmir import vesmir_cmd, vesmir_reaction_add
from anketa import anketa_cmd, vote_cmd
from simple_interactions import reply_on_mention
import webcheck.check as wch

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='.', intents=intents, help_command=None)

with open("config.json") as f:
    config = json.load(f)

with open("emojis.txt") as f:
    emojis = f.read().split(" ")

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    webcheck.start()

async def mark_random_emoji(message):
    emoji = random.choice(emojis)
    await message.add_reaction(emoji)
    return emoji

@client.event
async def on_message(message):
    a = client.process_commands(message)
    b = custom_on_message(message)
    await a
    await b
    
async def custom_on_message(message):
    if message.author == client.user:
        return
    await reply_on_mention(client.user, message)
    return
    await mark_random_emoji(message)

@client.event
async def on_reaction_add(reaction, user):
    await vesmir_reaction_add(reaction, user)
    
@client.command(name='anketa')
async def anketa(ctx):
    await anketa_cmd(ctx)

@client.command(name='vote')
async def vote(ctx):
    await vote_cmd(ctx)

@client.command(name='ahoj')
async def ahoj(ctx, *args):
    await ctx.channel.send(f"Ahoj!\n{args}")
    
@client.command(name='vesmir', aliases=['vesmír'])
async def vesmir(ctx):
    await vesmir_cmd(ctx)

@client.command(name='mark')
async def mark(ctx):
    messages = await ctx.channel.history(limit=10).flatten()
    for msg in messages:
        await mark_random_emoji(msg)

@tasks.loop(seconds=5)
async def webcheck():
    await wch.check(client, config["webcheck_channel_id"])
    


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.channel.send("Tenhle příkaz neznám :sadKuli:")
    else:
        print(error, file=sys.stderr)

#@client.event
#async def on_ready():
    #fp = open("stezbot_fang_500.png", 'rb')
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


client.run(config["token"]) 
