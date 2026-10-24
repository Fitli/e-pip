import asyncio
import json
import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable

# Alert when one container dies THRESHOLD times within WINDOW seconds,
# then stay quiet about that container for COOLDOWN seconds.
# Containers in the stop list are also stopped once they die STOP_THRESHOLD times.
THRESHOLD = 3
STOP_THRESHOLD = 5
WINDOW = 10 * 60
COOLDOWN = 60 * 60

_task = None


def start(client, user_id: int, stop_names: Iterable[str] = ()):
    """Start watching Docker in the background. Safe to call on every on_ready."""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_watch_forever(client, user_id, set(stop_names)))


async def _watch_forever(client, user_id: int, stop_names: set):
    while True:
        try:
            await _watch(client, user_id, stop_names)
        except Exception as e:
            print(f"dockerwatch: {e!r}")
        await asyncio.sleep(10)


async def _watch(client, user_id: int, stop_names: set):
    deaths: Dict[str, Deque[float]] = defaultdict(deque)
    last_alert: Dict[str, float] = {}
    proc = await asyncio.create_subprocess_exec(
        "docker", "events", "--filter", "type=container", "--filter", "event=die",
        "--format", "{{json .}}",
        stdout=asyncio.subprocess.PIPE,
    )
    print(f"dockerwatch: watching docker die events, may stop {sorted(stop_names)}")
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
            await _dm(client, user_id, text, f"alerted about {name}")

        if name in stop_names and len(q) >= STOP_THRESHOLD:
            logs = await _last_logs(name)
            if await _stop(name):
                # the die event from our own stop then counts as 1, below both thresholds
                q.clear()
                text = (
                    f"🛑 **hex**: kontejner `{name}` spadl {STOP_THRESHOLD}× za posledních "
                    f"{WINDOW // 60} min, zastavil jsem ho. Znovu spustit: "
                    f"`docker start {name}`\n```\n{logs}\n```"
                )
                await _dm(client, user_id, text, f"stopped {name}")
            else:
                await _dm(client, user_id, f"❌ **hex**: nepodařilo se zastavit `{name}`.",
                          f"failed to stop {name}")
    await proc.wait()
    raise RuntimeError("docker events stream ended")


async def _dm(client, user_id: int, text: str, what: str):
    try:
        user = await client.fetch_user(user_id)
        await user.send(text[:2000])
        print(f"dockerwatch: {what}")
    except Exception as e:
        print(f"dockerwatch: failed to DM ({what}): {e!r}")


async def _stop(name: str) -> bool:
    proc = await asyncio.create_subprocess_exec(
        "docker", "stop", "-t", "60", name,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    return await proc.wait() == 0


async def _last_logs(name: str, lines: int = 8) -> str:
    proc = await asyncio.create_subprocess_exec(
        "docker", "logs", "--tail", str(lines), name,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", out.decode(errors="replace"))
    return text.replace("```", "'''").strip()[-1200:]
