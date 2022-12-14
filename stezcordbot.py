import json
import sys

import discord
from discord.ext import commands, tasks
import random
from vesmir.vesmir import vesmir_cmd, vesmir_reaction_add
from voting.anketa import anketa_cmd, vote_cmd
from simple_interactions import reply_on_mention
import webcheck.check as wch
import archive.archive as archive

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='.', intents=intents, help_command=None)

with open("config.json") as f:
    config = json.load(f)

with open("voting/emojis.txt") as f:
    emojis = f.read().split(" ")

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    webcheck.start()
    archive_loop.start()

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
async def on_reaction_add(reaction: discord.Reaction, user):
    await vesmir_reaction_add(reaction, user)
    if archive.is_archive_msg(reaction.message.id):
        archive.delete_archivation(reaction.message.id)
    
@client.command(name='anketa')
async def anketa(ctx):
    await anketa_cmd(ctx)

@client.command(name='vote')
async def vote(ctx):
    await vote_cmd(ctx)

@client.command(name='ahoj')
async def ahoj(ctx, *args):
    await ctx.channel.send(f"Ahoj!\n{args}")

@client.command(name='help')
async def help(ctx):
    with open("webcheck/webs.json", "r") as webs:
        addrs = json.load(webs)
    addrs = [f"<{addr}>" for addr in addrs]
    weby = " a ".join(addrs)
    text = f"""
Ahoj! Jsem <@{client.user.id}>, stezčí Discord bot.

Momentálně umím příkazy:
- `.vote` = jednoduché hlasování ano/ne
- `.anketa` = vezmu všechny emoji obsažené ve zprávě a zareaguju s nimi, abyste mohli pohodlně hlasovat.
- `.help` vypíše tuto nápovědu
- `.sleduj` přidá nový web nebo weby do sledování
- `.nesleduj` odebere web nebo weby ze sledování
- `.zkontroluj_weby` zkontroluje okamžitě sledované weby
- `.archivuj` zaarchivuje kanál, do kterého se pošle příkaz. Ještě to ale může kdokoliv zvrátit.

Pravidelně sleduju weby {weby}, aby vám nic neuniklo. Pokud by se tam něco změnilo, napíšu do kanálu <#{config["webcheck_channel_id"]}>.

Ještě teda umím odesílat výkony z někdejší výzvy Pionýři do vesmíru, ale to teď už asi není zajímavý.

Můj vývoj má na starosti AS IT, zejména si se mnou hraje Vlk. Kdyby vás napadlo něco, co bych se měl naučit, řekněte jim.
"""
    await ctx.channel.send(text)
    
@client.command(name='vesmir', aliases=['vesmír'])
async def vesmir(ctx):
    await vesmir_cmd(ctx)

@client.command(name='mark')
async def mark(ctx):
    messages = await ctx.channel.history(limit=10).flatten()
    for msg in messages:
        await mark_random_emoji(msg)

@client.command(name='chcipni')
async def chcipni(ctx):
    await ctx.channel.send("Sbohem, krutý světe...")
    await client.close()

@tasks.loop(hours=2)
async def webcheck():
    await wch.check(client.get_channel(config["webcheck_channel_id"]))

@tasks.loop(hours=48)
async def archive_loop():
    await archive.archive_channels(client)
    
@client.command(name='sleduj')
async def sleduj(ctx):
    await wch.sleduj_cmd(ctx)

@client.command(name='nesleduj')
async def nesleduj(ctx):
    await wch.nesleduj_cmd(ctx)
    
@client.command(name='zkontroluj_weby')
async def zkontroluj_weby(ctx):
    await wch.zkontroluj_weby_cmd(ctx)

@client.command(name='archivuj')
async def archivuj(ctx):
    await archive.archive_cmd(ctx)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.channel.send("Tenhle příkaz neznám :sadKuli:")
    else:
        print(error, file=sys.stderr)



client.run(config["token"]) 
