from typing import Union

import discord
import requests
import re
import pprint

MEANSDICT = {
    '🚶': "pěšky",
    '🚴🏼': "kolo",
    '🛴': "koloběžka",
    '🛼': "brusle",
    '🏊': "plavání",
}

async def vesmir_cmd(ctx):
    data = parse_msg(ctx)
    await send_data(data, ctx)
    #msg = f"Našel jsem:\n{pprint.pformat(data)}"
    #await ctx.channel.send(msg)


async def send_data(data, ctx):
    embed = discord.Embed(title="Rozpoznal jsem aktivitu", colour=discord.Colour.green())
    embed.add_field(name="Pohybující se osoba", value=data["name"])
    embed.add_field(name="Vzdálenost", value=data["distance"])
    embed.add_field(name="Způsob přepravy", value=data["means of transport"])
    embed.add_field(name="Komentář", value=data["comment"], inline=False)
    embed.set_footer(text="Pro změnu typu přepravy použij reakci")
    msg = await ctx.channel.send(embed=embed)
    for emoji in MEANSDICT:
        await msg.add_reaction(emoji=emoji)
    await msg.add_reaction(emoji='❌')


def parse_msg(ctx):
    msg = ctx.message.content
    
    name = get_name(ctx)
    distance = get_distance(msg)
    comment = get_comment(msg)
    means_of_transport = get_means_of_transport(msg)
    
    return {
        "name": name,
        "distance": distance,
        "comment": comment,
        "means of transport": means_of_transport
    }

trdict = {
    "xkrumlov": "Vlk",
    "Drakis": "Zuby",
    "Targus": "Ledy",
    "pes": "Ola"
}

def get_name(ctx):
    person = ctx.author
    if len(ctx.message.mentions) > 0:
        person = ctx.message.mentions[0]
    if person.name in trdict:
        return trdict[person.name]
    nick = person.nick
    if nick:
        if nick in trdict:
            return trdict[nick]
        return nick
    return person.name

def get_distance(msg):
    mul = 1
    match = re.search("([0-9]*(?:.|,)?[0-9]*) (?:km|kilometr)", msg)
    if not match:
        mul = 1000
        match = re.search("([0-9]*(?:.|,)?[0-9]*) (?:m|metr)", msg)
    if not match:
        return None
    d = match.group(1)
    return float(d.replace(",", ".")) / mul

def get_comment(msg):
    comment = " ".join(msg.split(" ")[1:])
    if not comment:
        return None
    return comment

def get_means_of_transport(msg):
    if re.search("(?:kolobez|koloběž)", msg):
        return "koloběžka"
    if re.search("kol", msg):
        return "kolo"
    if re.search("brusl", msg):
        return "brusle"
    if re.search("plav", msg):
        return "plavání"
    return "pěšky"


async def vesmir_reaction_add(reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
    msg = reaction.message
    if msg.author.name != "Stezcord-bot": #TODO: better check of message
        return
    if user.name == "Stezcord-bot": #TODO: only author of activity can react
        return
    emoji = reaction.emoji
    if emoji in MEANSDICT:
        embed = msg.embeds[0]
        embed.set_field_at(2, name="Způsob přepravy", value=MEANSDICT[emoji])
        await msg.edit(embed=embed)
        await reaction.remove(user)
        return
    if emoji == '❌':
        await msg.delete()
        return
    await reaction.remove(user)


def send_request(data):
    responseurl = 'https://docs.google.com/forms/d/e/1FAIpQLScyghg2oS4cNLn5IUQJsCJystde-xPB1aESiAARh3alRK0d4A/formResponse'
    form_data = {
        "entry.2090870317": data["name"],       # Name
        "entry.900912904": data["distance"],    # distance [km]
        "entry.1648102255": data["comment"],    # comment
        "entry.1060833824_year": 2021,
        "entry.1060833824_month": 4,
        "entry.1060833824_day": 21,
        "entry.1318492768": "Pěšky",
        "fvv": 1,
        "draftResponse": [],
        "pageHistory": 0,
        "fbzx": 5173863167218276264,
        #"entry.1318492768_sentinel": "",
    }

    res = requests.post(responseurl, data=form_data)
    print(res)
    #print(res.text)
