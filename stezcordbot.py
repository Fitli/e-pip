import json
import discord

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return


    if message.content.startswith('$ahoj'):
        await message.channel.send("Ahoj!")


with open("config.json") as f:
    token = json.load(f)["token"]
client.run(token) 
