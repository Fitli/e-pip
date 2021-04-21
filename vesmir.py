import requests
import re
import pprint

async def vesmir_cmd(ctx):
    data = parse_msg(ctx)
    msg = f"Našel jsem:\n{pprint.pformat(data)}"
    await ctx.channel.send(msg)

def parse_msg(ctx):
    msg = ctx.message.content
    
    name = get_name(ctx)
    distance = get_distance(msg)
    comment = get_comment(msg)
    
    return {
        "name": name,
        "distance": distance,
        "comment": comment,
    }

trdict = {
    
}

def get_name(ctx):
    name = ctx.author.name
    if name in trdict:
        return trdict[name]
    nick = ctx.author.nick
    if nick:
        if nick in trdict:
            return trdict[nick]
        return nick
    return name

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
