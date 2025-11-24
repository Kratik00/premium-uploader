import time
from datetime import timedelta
from pyrogram.errors import FloodWait
import asyncio

# Size formatter
def hrb(value, digits=2, delim="", postfix=""):
    if value is None:
        return None
    chosen_unit = "B"
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        if value > 1000:
            value /= 1024
            chosen_unit = unit
        else:
            break
    return f"{value:.{digits}f}" + delim + chosen_unit + postfix

# Time formatter
def hrt(seconds, precision=0):
    pieces = []
    value = timedelta(seconds=seconds)
    if value.days:
        pieces.append(f"{value.days}d")
    seconds = value.seconds
    if seconds >= 3600:
        hours = int(seconds / 3600)
        pieces.append(f"{hours}h")
        seconds -= hours * 3600
    if seconds >= 60:
        minutes = int(seconds / 60)
        pieces.append(f"{minutes}m")
        seconds -= minutes * 60
    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}s")
    return "".join(pieces) if not precision else "".join(pieces[:precision])

# Simple progress bar
async def progress_bar(current, total, reply, start):
    # Only update once at the end for best performance
    if current == total:
        end = time.time()
        duration = hrt(end - start, precision=2)
        size = hrb(total)
        try:
            await reply.edit(f"✅ **Upload complete!**\n📦 Size: `{size}`\n⏱️ Time: `{duration}`")
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await reply.edit(f"✅ **Upload complete!**\n📦 Size: `{size}`\n⏱️ Time: `{duration}`")
