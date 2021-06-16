from datetime import date, timedelta
from typing import Union, List

import random
import discord
import requests
import re


open_actions = {}

CHANNEL_NAME = "pionýři-do-vesmíru"
MEANS_DICT = {
    '🚶': "Pěšky",
    '🚴🏼': "Kolo",
    '🛴': "Koloběžka",
    '🛼': "Brusle",
    '🏊': "Plavání",
    '🚣': "Loď"
}

MOTIVATION_QUOTES = [
    "Blížíme se k Měsíci!",
    "Země za zády je čím dál menší!",
    "Doufám, že tě z toho moc nebolí nohy.",
    "Upravujeme kurz."
]


class Action:
    def __init__(self, names: List[str], distance: float, comment: str, means_of_transport: str,
                 activity_date: date, ctx, author: discord.abc.User):
        self.names = names
        self.distance = distance
        self.comment = comment
        self.means = means_of_transport
        self.date = activity_date
        self.ctx = ctx
        self.author = author
        self.msg = None

    async def send_embed(self):
        embed = discord.Embed(title="Rozpoznal jsem aktivitu", colour=discord.Colour.gold())
        if len(self.names) == 1:
            embed.add_field(name="Pohybující se osoba", value=self.names[0])
        else:
            embed.add_field(name="Pohybující se osoby", value=", ".join(self.names))
        embed.add_field(name="Vzdálenost", value=str(self.distance))
        embed.add_field(name="Způsob přepravy", value=self.means)
        embed.add_field(name="Datum", value=self.date.strftime("%-d. %-m."))
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
        if user == self.ctx.me:
            return
        if user != self.author:
            await reaction.remove(user)
            return
        emoji = reaction.emoji
        if emoji in MEANS_DICT:
            self.means = MEANS_DICT[emoji]
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
        self.send_request()
        embed = self.msg.embeds[0]
        embed.title = "Odeslal jsem aktivitu"
        embed.colour = discord.Colour.blue()
        embed.set_footer(text=random.choice(MOTIVATION_QUOTES))
        await self.msg.edit(embed=embed)
        await self.msg.clear_reactions()
        open_actions.pop(self.msg.id)

    def send_request(self):
        responseurl = 'https://docs.google.com/forms/d/e/1FAIpQLScyghg2oS4cNLn5IUQJsCJystde-xPB1aESiAARh3alRK0d4A/formResponse'
        for name in self.names:
            form_data = {
                "entry.2090870317": name,  # Name
                "entry.900912904": str(self.distance).replace(".", ","),  # distance [km]
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
    if ctx.channel.name != CHANNEL_NAME:
        return
    action = await parse_msg(ctx)
    if action:
        await action.send_embed()


async def parse_msg(ctx):
    msg = ctx.message.content.lower()
    author = ctx.message.author
    
    name = get_name(ctx)
    distance = get_distance(msg)
    if distance is None:
        await ctx.channel.send("Nikde tu nevidím vzdálenost :sadKuli:")
        return None
    comment = get_comment(msg)
    means_of_transport = get_means_of_transport(msg)
    activity_date = get_date(msg)
    if activity_date < date(2021, 4, 14):
        await ctx.channel.send(f"Tak hele mantáku, datum {activity_date.strftime('%-d. %-m. %Y')} je před "
                               f"začátkem výzvy, to se nepočítá")
        return None
    if activity_date > date.today():
        await ctx.channel.send(f"{activity_date.strftime('%-d. %-m. %Y')}? Jestli máš stroj času, nech "
                               f"mě taky projet, chtěl bych vidět roboty za 100 let")
        return None
    
    return Action(name, distance, comment, means_of_transport, activity_date, ctx, author)


trdict = {
    "xkrumlov": "Vlk",
    "Drakis": "Zuby",
    "Targus": "Ledy",
    "pes": "Ola",
    "Wudiap": "Kulihrášek",
    "Atom": "Ota",
    "MRQA": "Mrqa",
    "TAKY": "Taky",
    "Elis": "Eliška"
}


def get_name(ctx):
    persons = [ctx.author]
    if len(ctx.message.mentions) > 0:
        persons = ctx.message.mentions
    return [name_from_user(p) for p in persons]


def name_from_user(person):
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
    match = re.search(r"([0-9]+(?:.|,)?[0-9]*) *(?:km\b|kilometr)", msg)
    if not match:
        mul = 1000
        match = re.search(r"([0-9]+(?:.|,)?[0-9]*) *(?:m\b|metr)", msg)
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
    if re.search(r"(\bkolobez|\bkoloběž)", msg):
        return "Koloběžka"
    if re.search(r"(\bkol(e(?!m)|o)|cykl)", msg):
        return "Kolo"
    if re.search("brusl", msg):
        return "Brusle"
    if re.search("plav", msg):
        return "Plavání"
    if re.search(r"\blod|\bloď|pádl", msg):
        return "Loď"
    return "Pěšky"


def get_date(msg):
    if re.search(r"\bdnes", msg):
        return date.today()
    if re.search(r"\bpředevčírem\b|\bpredevcirem\b|\bpředvčer|\bpredvcer", msg):
        return date.today() - timedelta(days=2)
    if re.search(r"\bvčer|\bvcer", msg):
        return date.today() - timedelta(days=1)
    match = re.search(r"([0-9]{1,2})\. *([0-9]{1,2})\.", msg)
    if match:
        return date(2021, int(match.group(2)), int(match.group(1)))
    match = re.search(r"([0-9]{1,2})\. *dubna", msg)
    if match:
        return date(2021, 4, int(match.group(1)))
    match = re.search(r"([0-9]{1,2})\. *(května|kvetna)", msg)
    if match:
        return date(2021, 5, int(match.group(1)))
    match = re.search(r"([0-9]{1,2})\. *(června|cervna)", msg)
    if match:
        return date(2021, 6, int(match.group(1)))
    return date.today()


async def vesmir_reaction_add(reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
    msg_id = reaction.message.id
    if msg_id in open_actions:
        await open_actions[msg_id].reaction_add(reaction, user)
