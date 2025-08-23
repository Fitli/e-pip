from opengraph_parse import parse_page
import re

async def get_album_covers(ctx):
    urls = get_urls(ctx)
    covers = []
    for url in urls:
        og = parse_page(url)
        covers.append(get_cover_html(url, og))

    covers = '\n'.join(covers)
    await ctx.channel.send(f"""Toto vložte na [web](https://stezka.org/wp-admin/post.php?post=271&action=edit) a zaškrtněte fotky v [tabulce](https://docs.google.com/spreadsheets/d/1GURZ_Z6NE7TgClyhxkbgwaRp4qBWTHeGrwpuIqsbSRU/edit?gid=0#gid=0):\n```html\n{covers}\n```""")

def get_cover_html(url, og):
    title = og['og:title'].replace(" [", "<br>[")
    title = re.sub(r" ·.*", "", title)
    return f"""<a class="preview-a" href="{url}"><div class="preview-wrap"><img src="{og['og:image']}"></img><div class="preview-title">{title}</div></div></a>"""


def get_urls(ctx):
    msg = ctx.message.content
    addrs_m = re.findall(r"((https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))", msg)
    # print(addrs_m)
    addrs = []
    if not addrs_m:
        return addrs
    for addr_m in addrs_m:
        addr = addr_m[0]
        if addr_m[1] == "":
            addr = "http://" + addr
        addrs.append(addr)
    return addrs
