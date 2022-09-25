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

async def check(client, channel_id):
    message_channel = client.get_channel(channel_id)
    
    with open("webcheck/webs.json", "r") as webs:
        state = json.load(webs)

    for addr in state:
        h = download(addr)
        if h != state[addr]:
            await message_channel.send(f"Nastala změna na webu {addr}!")
            state[addr] = h
    
    with open("webcheck/webs.json", "w") as webs:
        json.dump(state, webs)

def download(addr):
    r = requests.get(addr)
    if not r.ok:
        print(f"can't reach {addr}")
        return -1
    else:
        return myHash(r.text)
