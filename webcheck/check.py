import json
import requests
import re

def myHash(text:str):
    text = re.sub(r'([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?', '', text)
    text = re.sub(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', '', text)
    hash=0
    for ch in text:
        hash = ( hash*59611  ^ ord(ch)*65543) & 0xFFFFFFFF
    return hash

async def check(message_channel, no_change=False):
    with open("webcheck/webs.json", "r") as webs:
        state = json.load(webs)

    changed = False
    for addr in state:
        h = download(addr)
        if h != state[addr]:
            await message_channel.send(f"Nastala změna na webu <{addr}>!")
            state[addr] = h
            changed = True
    if no_change and not changed:
        await message_channel.send(f"Nenastala žádná změna")
    
    with open("webcheck/webs.json", "w") as webs:
        json.dump(state, webs)

def download(addr):
    r = requests.get(addr)
    if not r.ok:
        print(f"can't reach {addr}")
        return -1
    else:
        return myHash(r.text)

def get_urls(ctx):
    msg = ctx.message.content
    addrs_m = re.findall(r"((https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))", msg)
    print(addrs_m)
    addrs = []
    if not addrs_m:
        return addrs
    for addr_m in addrs_m:
        addr = addr_m[0]
        if addr_m[1] == "":
            addr = "http://" + addr
        addrs.append(addr)
    return addrs
    

async def sleduj_cmd(ctx):
    addrs = get_urls(ctx)
    if not addrs:
        await ctx.message.channel.send("Nenašel jsem žádnou validní URL adresu!")
        return
    
    with open("webcheck/webs.json", "r") as webs:
        state = json.load(webs)
    
    for addr in addrs:  
        if not addr in state:
            h = download(addr)
            state[addr] = h
            await ctx.message.channel.send(f"Přidávám {addr}.")
        else:
            await ctx.message.channel.send(f"{addr} už sleduju.")
    
    with open("webcheck/webs.json", "w") as webs:
        json.dump(state, webs)


async def nesleduj_cmd(ctx):
    addrs = get_urls(ctx)
    if not addrs:
        await ctx.message.channel.send("Nenašel jsem žádnou validní URL adresu!")
        return
    
    with open("webcheck/webs.json", "r") as webs:
            state = json.load(webs)

    for addr in addrs:
        if addr in state:
            state.pop(addr)
            await ctx.message.channel.send(f"Odstraňuju {addr}.")
        else:
            await ctx.message.channel.send(f"{addr} jsem nesledoval.")
    
    with open("webcheck/webs.json", "w") as webs:
        json.dump(state, webs)


async def zkontroluj_weby_cmd(ctx):
    await check(ctx.channel, no_change=True)
