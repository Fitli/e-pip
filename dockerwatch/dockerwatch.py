import asyncio
import json
import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict

# Alert when one container dies THRESHOLD times within WINDOW seconds,
# then stay quiet about that container for COOLDOWN seconds.
THRESHOLD = 3
WINDOW = 10 * 60
COOLDOWN = 60 * 60

_task = None


def start(client, user_id: int):
    """Start watching Docker in the background. Safe to call on every on_ready."""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_watch_forever(client, user_id))


async def _watch_forever(client, user_id: int):
    while True:
        try:
            await _watch(client, user_id)
        except Exception as e:
            print(f"dockerwatch: {e!r}")
        await asyncio.sleep(10)


async def _watch(client, user_id: int):
    deaths: Dict[str, Deque[float]] = defaultdict(deque)
    last_alert: Dict[str, float] = {}
    proc = await asyncio.create_subprocess_exec(
        "docker", "events", "--filter", "type=container", "--filter", "event=die",
        "--format", "{{json .}}",
        stdout=asyncio.subprocess.PIPE,
    )
    print("dockerwatch: watching docker die events")
    async for line in proc.stdout:
        attrs = json.loads(line).get("Actor", {}).get("Attributes", {})
        name = attrs.get("name", "?")
        now = time.time()

        q = deaths[name]
        q.append(now)
        while q and now - q[0] > WINDOW:
            q.popleft()

        if len(q) >= THRESHOLD and now - last_alert.get(name, 0) > COOLDOWN:
            last_alert[name] = now
            text = (
                f"⚠️ **hex**: kontejner `{name}` spadl {len(q)}× za posledních "
                f"{WINDOW // 60} min (exit code {attrs.get('exitCode', '?')}). "
                f"Nejspíš crash loop.\n```\n{await _last_logs(name)}\n```"
            )
            try:
                user = await client.fetch_user(user_id)
                await user.send(text[:2000])
                print(f"dockerwatch: alerted about {name}")
            except Exception as e:
                print(f"dockerwatch: failed to alert about {name}: {e!r}")
    await proc.wait()
    raise RuntimeError("docker events stream ended")


async def _last_logs(name: str, lines: int = 8) -> str:
    proc = await asyncio.create_subprocess_exec(
        "docker", "logs", "--tail", str(lines), name,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", out.decode(errors="replace"))
    return text.replace("```", "'''").strip()[-1200:]
