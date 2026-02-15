import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

from discord import abc, utils
from discord.ext import commands

ARCHIVE_FILE = "persistent/data/arch_categories.json"

open_archivations: Dict[int, Tuple[datetime, int]] = {}


def get_archive_category(channel: abc.GuildChannel) -> Optional[int]:
    category = channel.category.id
    with open(ARCHIVE_FILE, "r") as cats:
        arch_categories: Dict[str, int] = json.load(cats)
    return arch_categories.get(str(category))


async def archive_chanel(client, channel_id: int):
    channel: abc.GuildChannel = client.get_channel(channel_id)

    cat = utils.get(channel.guild.categories, id=get_archive_category(channel))

    await channel.move(end=True, category=cat)


def is_archive_msg(message_id: int) -> bool:
    return message_id in open_archivations


def delete_archivation(msg_id: int):
    open_archivations.pop(msg_id)


async def archive_cmd(ctx: commands.Context):
    archive_time = datetime.now() + timedelta(days=2)
    msg = await ctx.channel.send(
        f"Tento kanál bude v nejbližší době ({archive_time.date()}) archivován. Pokud tomu chcete "
        f"zabránit, dejte libovolnou reakci na tuto zprávu a proces bude zastaven.")
    open_archivations[msg.id] = (archive_time, ctx.channel.id)


async def archive_channels(client):
    for msg, (time, channel_id) in list(open_archivations.items()):
        if datetime.now() > time:
            await archive_chanel(client, channel_id)
            delete_archivation(msg)
