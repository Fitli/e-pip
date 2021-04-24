from datetime import date, timedelta
from typing import Union

import discord
import requests
import re


open_actions = {}


MEANS_DICT = {
    '🚶': "pěšky",
    '🚴🏼': "kolo",
    '🛴': "koloběžka",
    '🛼': "brusle",
    '🏊': "plavání",
}


class Action:
    def __init__(self, name: str, distance: float, comment: str, means_of_transport: str,
                 activity_date: date, ctx, author: discord.abc.User):
        self.name = name
        self.distance = distance
        self.comment = comment
        self.means = means_of_transport
        self.date = activity_date
        self.ctx = ctx
        self.author = author
        self.msg = None

    async def send_embed(self):
        embed = discord.Embed(title="Rozpoznal jsem aktivitu", colour=discord.Colour.gold())
        embed.add_field(name="Pohybující se osoba", value=self.name)
        embed.add_field(name="Vzdálenost", value=str(self.distance))
        embed.add_field(name="Způsob přepravy", value=self.means)
        embed.add_field(name="Datum", value=str(self.date))
        embed.add_field(name="Komentář", value=self.comment, inline=False)
        embed.set_footer(text="Pro změnu typu přepravy použij reakci.\n"
                              + "Pomocí ❌ můžeš aktivitu zrušit, pomocí 🚀 odeslat")
        msg = await self.ctx.channel.send(embed=embed)
        self.msg = msg
        for emoji in MEANS_DICT:
            await msg.add_reaction(emoji=emoji)
        await msg.add_reaction(emoji='❌')
        await msg.add_reaction(emoji='🚀')
        open_actions[msg.id] = self

    async def reaction_add(self, reaction: discord.Reaction,
                           user: Union[discord.Member, discord.User]):
        if user.name == "Stezcord-bot":
            return
        if user != self.author:
            await reaction.remove(user)
            return
        emoji = reaction.emoji
        if emoji in MEANS_DICT:
            embed = self.msg.embeds[0]
            embed.set_field_at(2, name="Způsob přepravy", value=MEANS_DICT[emoji])
            await self.msg.edit(embed=embed)
            await reaction.remove(user)
            return
        if emoji == '❌':
            await self.msg.delete()
            return
        if emoji == '🚀':
            await self.send()
            return
        await reaction.remove(user)

    async def send(self):
        #self.send_request()
        embed = self.msg.embeds[0]
        embed.title = "Odeslal jsem aktivitu"
        embed.colour = discord.Colour.blue()
        embed.set_footer(text="Blížíme se k měsíci!")
        await self.msg.edit(embed=embed)
        open_actions.pop(self.msg.id)

    def send_request(self):
        responseurl = 'https://docs.google.com/forms/d/e/1FAIpQLScyghg2oS4cNLn5IUQJsCJystde-xPB1aESiAARh3alRK0d4A/formResponse'
        form_data = {
            "entry.2090870317": self.name,  # Name
            "entry.900912904": self.distance,  # distance [km]
            "entry.1648102255": self.comment,  # comment
            "entry.1060833824_year": self.date.year,
            "entry.1060833824_month": self.date.month,
            "entry.1060833824_day": self.date.day,
            "entry.1318492768": self.means,
            "fvv": 1,
            "draftResponse": [],
            "pageHistory": 0,
            "fbzx": 5173863167218276264,
            # "entry.1318492768_sentinel": "",
        }

        res = requests.post(responseurl, data=form_data)
        print(res)
        # print(res.text)


async def vesmir_cmd(ctx):
    action = parse_msg(ctx)
    await action.send_embed()


def parse_msg(ctx):
    msg = ctx.message.content
    author = ctx.message.author
    
    name = get_name(ctx)
    distance = get_distance(msg)
    comment = get_comment(msg)
    means_of_transport = get_means_of_transport(msg)
    activity_date = get_date(msg)
    
    return Action(name, distance, comment, means_of_transport, activity_date, ctx, author)


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
    match = re.search("([0-9]+(?:.|,)?[0-9]*) (?:km|kilometr)", msg)
    if not match:
        mul = 1000
        match = re.search("([0-9]+(?:.|,)?[0-9]*) (?:m|metr)", msg)
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


def get_date(msg):
    if re.search("dnes", msg):
        return date.today()
    if re.search("včera|vcera", msg):
        return date.today() - timedelta(days=1)
    if re.search("předevčírem|predevcirem", msg):
        return date.today() - timedelta(days=2)
    match = re.search("([0-9]{1,2}). ([0-9]{1,2}).", msg)
    if match:
        return date(2021, int(match.group(2)), int(match.group(1)))
    return date.today()


async def vesmir_reaction_add(reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
    msg_id = reaction.message.id
    if msg_id in open_actions:
        await open_actions[msg_id].reaction_add(reaction, user)
