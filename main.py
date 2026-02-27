import os
import re
import sys
import m3u8
import json
import time
import pytz
import httpx
import asyncio
import requests
import subprocess
import urllib
import urllib.parse
import yt_dlp
import tgcrypto
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
from logs import logging
from bs4 import BeautifulSoup
import saini as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, MONGO_URL
from aiohttp import ClientSession
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
import random
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMembersFilter, ChatType
import aiohttp
import aiofiles
import zipfile
import shutil
import ffmpeg
from datetime import datetime, timedelta
import pytz
from motor.motor_asyncio import AsyncIOMotorClient

mongo = AsyncIOMotorClient(MONGO_URL)
premium_db = mongo["premiumbot"]["premiumbot_users"]

# Initialize the bot
bot = Client(
    "bot",
    api_id= "28712726",
    api_hash= "06acfd441f9c3402ccdb1945e8e2a93b",
    bot_token= "8239749246:AAHpajo4unqhY_hZth1NgiZf8dPL0MvaeHA"
)

processing_request = False
cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url = "http://master-api-v3.vercel.app/"
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
token_cp ='eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTExOTM1ODYzLCJvcmdJZCI6NDA1NDczLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwMTQ4OTg2NjgiLCJuYW1lIjoieW9nZXNoIE1haGF3YXIiLCJlbWFpbCI6ImtvaGxpa2FtaW5hMzRAZ21haWwuY29tIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJkZWZhdWx0TGFuZ3VhZ2UiOiJFTiIsImNvdW50cnlDb2RlIjoiSU4iLCJjb3VudHJ5SVNPIjoiOTEiLCJ0aW1lem9uZSI6IkdNVCs1OjMwIiwiaXNEaXkiOnRydWUsIm9yZ0NvZGUiOiJqY3d2ayIsImlzRGl5U3ViYWRtaW4iOjAsImZpbmdlcnByaW50SWQiOiIwNzZkY2YzNTFjZGE0OTQ4YWI5OWVmOTUyNTZhNGRjZiIsImlhdCI6MTc1MDc2NDA2NSwiZXhwIjoxNzUxMzY4ODY1fQ.2zOo-wjMu6UDGfTq-XKoWugWX02rTWkkR6brGPlrkfJi0k-SIPDPSo3HXzsaa6on'
adda_token = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJkcGthNTQ3MEBnbWFpbC5jb20iLCJhdWQiOiIxNzg2OTYwNSIsImlhdCI6MTc0NDk0NDQ2NCwiaXNzIjoiYWRkYTI0Ny5jb20iLCJuYW1lIjoiZHBrYSIsImVtYWlsIjoiZHBrYTU0NzBAZ21haWwuY29tIiwicGhvbmUiOiI3MzUyNDA0MTc2IiwidXNlcklkIjoiYWRkYS52MS41NzMyNmRmODVkZDkxZDRiNDkxN2FiZDExN2IwN2ZjOCIsImxvZ2luQXBpVmVyc2lvbiI6MX0.0QOuYFMkCEdVmwMVIPeETa6Kxr70zEslWOIAfC_ylhbku76nDcaBoNVvqN4HivWNwlyT0jkUKjWxZ8AbdorMLg"
photologo = 'https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png' #https://envs.sh/GV0.jpg
photoyt = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png' #https://envs.sh/GVi.jpg
photocp = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'
photozip = 'https://envs.sh/cD_.jpg'

# 🔹 Add / Update Premium
async def add_premium_user(user_id: int, expire: datetime):
    await premium_db.update_one(
        {"_id": user_id},
        {"$set": {"expire_date": expire}},
        upsert=True
    )


# 🔹 Remove Premium
async def remove_premium_user(user_id: int):
    await premium_db.delete_one({"_id": user_id})


# 🔹 Get Raw Premium Data
async def check_premium_user(user_id: int):
    return await premium_db.find_one({"_id": user_id})


# 🔹 Get All Premium Users
def get_all_premium():
    return premium_db.find({})


# 🔹 Boolean Premium Check (Main Logic)
async def is_premium_user(user_id: int) -> bool:
    user = await premium_db.find_one({"_id": user_id})

    if not user:
        return False

    expire_date = user.get("expire_date")
    if not expire_date:
        return False

    # Convert both to naive UTC
    now = datetime.utcnow()
    expire_date = expire_date.replace(tzinfo=None)

    if expire_date < now:
        # Auto remove expired user
        await premium_db.delete_one({"_id": user_id})
        return False

    return True


# 🔹 Premium Access Check (Private + Admin Based)
async def check_premium_access(bot: Client, m: Message):

    # Private Chat
    if m.chat.type == ChatType.PRIVATE:
        if not m.from_user:
            return False
        return await is_premium_user(m.from_user.id)

    # Group / Supergroup / Channel
    try:
        async for admin in bot.get_chat_members(
            m.chat.id,
            filter=ChatMembersFilter.ADMINISTRATORS
        ):
            if await is_premium_user(admin.user.id):
                return True
    except ChatAdminRequired:
        return False

    return False
@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )

    try:
        # Wait for the user to send the cookies file
        input_message: Message = await client.listen(m.chat.id)

        # Validate the uploaded file
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        # Download the cookies file
        downloaded_path = await input_message.download()

        # Read the content of the uploaded file
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        # Replace the content of the target cookies file
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")
        
@bot.on_message(filters.command("add_premium"))
async def add_premium_cmd(client, message):

    if message.from_user.id != OWNER_ID:
        return await message.reply("Only owner can use this.")

    if len(message.command) != 3:
        return await message.reply("Usage:\n`/add_premium user_id days`")

    uid = int(message.command[1])
    days = int(message.command[2])

    # Store as naive UTC
    expire = datetime.utcnow() + timedelta(days=days)

    await add_premium_user(uid, expire)

    # Convert for display (attach UTC tz first)
    expire_ist = (
        expire.replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone("Asia/Kolkata"))
        .strftime("%d-%m-%Y %I:%M %p")
    )

    await message.reply(f"⭐ Premium given to `{uid}`\nExpires: `{expire_ist}`")

    try:
        await client.send_message(uid, f"🔥 You are now premium till {expire_ist}")
    except:
        pass

@bot.on_message(filters.command("remove_premium"))
async def remove_premium_cmd(client, message):

    if message.from_user.id != OWNER_ID:
        return await message.reply("Only owner can use this.")

    if len(message.command) != 2:
        return await message.reply("Usage: `/remove_premium user_id`")

    uid = int(message.command[1])

    await remove_premium_user(uid)

    await message.reply("Removed successfully.")

    try:
        await client.send_message(uid, "Your premium is removed.")
    except:
        pass

@bot.on_message(filters.command("premium_users"))
async def premium_users_cmd(client, message):

    if message.from_user.id != OWNER_ID:
        return await message.reply("Only owner can use this.")

    cursor = get_all_premium()
    users = await cursor.to_list(length=None)

    if not users:
        return await message.reply("No premium users.")

    text = "👑 **ACTIVE PREMIUM USERS:**\n\n"

    for i, u in enumerate(users, start=1):
        expire = u["expire_date"]

        expire_ist = (
            expire.replace(tzinfo=pytz.utc)
            .astimezone(pytz.timezone("Asia/Kolkata"))
            .strftime("%d-%m-%Y %I:%M %p")
        )

        text += f"{i}. `{u['_id']}`\n⏳ Till: `{expire_ist}`\n\n"

    await message.reply(text)

@bot.on_message(filters.command("chk_premium"))
async def chk_premium_cmd(client, message):

    if len(message.command) != 2:
        return await message.reply("Usage: `/chk_premium user_id`")

    uid = int(message.command[1])

    data = await check_premium_user(uid)

    if not data:
        return await message.reply("Not premium.")

    expire = data["expire_date"]

    expire_ist = (
        expire.replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone("Asia/Kolkata"))
        .strftime("%d-%m-%Y %I:%M %p")
    )

    await message.reply(f"YES PREMIUM\nTill `{expire_ist}`")
   
        
@bot.on_message(filters.command(["stop"]) )
async def restart_handler(_, m):
    await m.reply_text("👾**STOPPED BABY**👾", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(f"<blockquote>The ID of this chat id is: </blockquote>`{chat_id}`")

@bot.on_message(filters.command(["upload"]))
async def txt_handler(bot: Client, m: Message):

    if not await check_premium_access(bot, m):
        return await m.reply_text(
            "**❌ Premium Required**\n\n"
            "This feature is only available for premium users."
        )

    try:
        await m.delete()
    except:
        pass

    editable = await m.reply_text("**⚡𝗦𝖾𝗇𝖽 𝗧𝗑𝗍 𝗙𝗂𝗅𝖾⚡**")

    input_msg: Message = await bot.listen(editable.chat.id)

    y = await input_msg.download()
    await input_msg.delete(True)

    file_name, ext = os.path.splitext(os.path.basename(y))

    if file_name.endswith("_helper"):  # ✅ Check if filename ends with "_helper"
        x = decrypt_file_txt(y)  # Decrypt the file
        await input.delete(True)
    else:
        x = y 

    path = f"./downloads/{m.chat.id}"
    pdf_count = 0
    img_count = 0
    zip_count = 0
    other_count = 0
    
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        
        links = []
        for i in content:
            if "://" in i:
                url = i.split("://", 1)[1]
                links.append(i.split("://", 1))
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif ".zip" in url:
                    zip_count += 1
                else:
                    other_count += 1
        os.remove(x)
    except:
        await m.reply_text("<pre><code>🔹Invalid file input.</code></pre>")
        os.remove(x)
        return
    
    await editable.edit(
        f"🔹Total Links: {len(links)}\n\n"
        "1️⃣ Start Index\n"
        "2️⃣ Batch Name (or 1)\n"
        "3️⃣ Quality (144/240/360/480/720/1080)\n"
        "4️⃣ Your Name (or 1)\n"
        "5️⃣ PW Token (or /anything)\n"
        "6️⃣ Thumb URL (or /d or No)\n\n"
    )
    try:
        input_all: Message = await bot.listen(
            editable.chat.id,
            filters=filters.user(m.from_user.id) if m.from_user else None,
            timeout=180
        )
    except asyncio.TimeoutError:
        await editable.delete()
        return await m.reply_text("⏰ Session expired. Use /upload again.")
        
    if input_all.text.lower() in ["/cancel", "cancel"]:
        await editable.delete()
        return await m.reply_text("❌ Upload cancelled.")
        
    data = input_all.text.strip().split("\n")
    await input_all.delete(True)
    
    if len(data) < 6:
        await editable.delete()
        return await m.reply_text("❌ Invalid format. Send exactly 6 lines.")
        
    raw_text = data[0].strip()
    raw_text0 = data[1].strip()
    raw_text2 = data[2].strip()
    raw_text3 = data[3].strip()
    raw_text4 = data[4].strip()
    raw_text6 = data[5].strip()
    
    count = int(raw_text)
    arg = int(raw_text)
    
    if raw_text0 == "1":
        b_name = file_name.replace('_', ' ')
    else:
        b_name = raw_text0
        
    quality = f"{raw_text2}p"
    quality_map = {
        "144": "256x144",
        "240": "426x240",
        "360": "640x360",
        "480": "854x480",
        "720": "1280x720",
        "1080": "1920x1080"
    }
    
    res = quality_map.get(raw_text2, "UN")
    
    if raw_text3 == "1":
        CR = '[LUCIFER](https://t.me/NOOBHUSIR)'
    else:
        CR = raw_text3
        
    if raw_text6.lower() == "no" or raw_text6 == "/d":
        thumb = None
    elif raw_text6.startswith("http://") or raw_text6.startswith("https://"):
        getstatusoutput(f"wget '{raw_text6}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = raw_text6
        
    await editable.delete()
    sent_msg = await bot.send_message(
        m.chat.id,
        f"__**🎯Target Batch : {b_name}**__"
    )
    
    if m.chat.type != ChatType.PRIVATE:
        try:
            await sent_msg.pin(disable_notification=True)
        except:
            pass

    failed_count = 0
    count =int(raw_text)    
    arg = int(raw_text)
    try:
        for i in range(arg-1, len(links)):
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            link0 = "https://" + Vxy

            name1 = links[i][0].replace("(", "[").replace(")", "]").replace("_", "").replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{name1[:60]}'
            
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            
            elif "rozgarapinew" in url:
                url = f"https://player-f005d2957c8b.herokuapp.com/play?url={url}"
                
            elif "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'

            elif "edge.api.brightcove.com" in url:
                    new_bcov_token = "bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NDc0NzY5MzEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiUkZCSFpGUmhObWhEZFhZMFNUSTFhM0FyU1RVemR6MDkiLCJmaXJzdF9uYW1lIjoiTldwbGFWcFNOVXRUTm1sU1JFdGpLelpuYm1SQ1FUMDkiLCJlbWFpbCI6IlkxaHdNelZVUTFjeE1IQmpTMmhDYVdWYVZuRkZlazVwWVRKbU4zbGFkRGhJV1VWbVNHRktVV3BoY3owPSIsInBob25lIjoiZWtZdk1rUmxURVpEZURSdlUyaHpZbGRpV0drM2R6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJhemhKSzNwbFZHeDFXa2xKYWxWTFdscEpiMEphUVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiWGlhb21pIE0yMDA3SjIwQ0kiLCJyZW1vdGVfYWRkciI6IjE4LjIxMy4xMTUuMTA1In19.hUp4gzFCXKUg6jhosLP0YXkHHAvU7K9uwXT22k02UALahUtcRI_EwVnVaheS54n-GUBCvFjQokhqsNfWyNTiljbx_hRAA19X67qzTBU8qdJuNxfhgKloGpR9aB7qybkqN4QzOBliSb7JNPAICQ_TtfUIqH1N5DCnLldvBBLoayejefCTTe012VHHkTCnsp3HnypcgMFu5Tsaw-Gvzz80e6RwlWVgivU5s2h9OtMgbrKMVbvnsvnRQS08zbu0Z7-4ZN_HzfoQ9SGliXqlpxJKVZCCBwHM5UVUTSqMNamHv-YnsjPVfAJoOTzkRY0Ka_AU5SWSXJhpPqh7fHGWtT8KYw"
                    
                    # Remove any existing bcov_auth if present
                    if "bcov_auth=" in url:
                        url = url.split("bcov_auth=")[0].rstrip("?&")
                    
                    # Add new token with proper separator
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}{new_bcov_token}"

            elif "https://static-wsb.classx.co.in/" in url:
                clean_url = url.split("?")[0]

                clean_url = clean_url.replace("https://static-wsb.classx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")

                url = clean_url

            elif "https://static-db.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")


            elif "https://static-db-v2.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")


            elif "https://static-wsb.appx.co.in/" in url:
                clean_url = url.split("?")[0]

                clean_url = clean_url.replace("https://static-wsb.appx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")

                url = clean_url

            elif "https://static-db.appx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db.appx.co.in", "https://appxcontent.kaxa.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db.appx.co.in", "https://appxcontent.kaxa.in")


            elif "https://static-db-v2.appx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db-v2.appx.co.in", "https://appx-content-v2.classx.co.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db-v2.appx.co.in", "https://appx-content-v2.classx.co.in")

           
            elif "/khansirvod4" in url and "akamaized" in url:
                 url = url.replace(url.split("/")[-1], raw_text2+".m3u8")
 

# --- Unified Classplus/Testbook handler using ITSGOLU API ---
            if any(x in url for x in ["https://cpvod.testbook.com/", "classplusapp.com/drm/", "media-cdn.classplusapp.com", "media-cdn-alisg.classplusapp.com", "media-cdn-a.classplusapp.com", "tencdn.classplusapp", "videos.classplusapp", "webvideos.classplusapp.com"]):
                # normalize cpvod -> media-cdn path used by API
                url_norm = url.replace("https://cpvod.testbook.com/", "https://media-cdn.classplusapp.com/drm/")
                api_url_call = f"https://shefu-api-final.vercel.app/shefu?url={url_norm}@ITSGOLU_FORCE&user_id=8415922431"
                keys_string = ""
                mpd = None
                try:
                    resp = requests.get(api_url_call, timeout=30)
                    data = resp.json()

                    # DRM response (MPD + KEYS)
                    if isinstance(data, dict) and "KEYS" in data and "MPD" in data:
                        mpd = data.get("MPD")
                        keys = data.get("KEYS", [])
                        url = mpd
                        keys_string = " ".join([f"--key {k}" for k in keys])
                        print(f"✅ DRM Content - Got {len(keys)} keys")

                    # Non-DRM response (direct url)
                    elif isinstance(data, dict) and "url" in data:
                        url = data.get("url")
                        keys_string = ""
                        print("✅ Non-DRM Content - Got direct URL")

                    else:
                        # Unexpected response format
                        await m.reply_text("⚠️ API returned unexpected response, attempting fallback...")
                        # Try helper fallback that used to work for drm-only endpoints
                        try:
                            res = helper.get_mps_and_keys2(url_norm)
                            if res:
                                mpd, keys = res
                                url = mpd
                                keys_string = " ".join([f"--key {k}" for k in keys])
                                print("🔁 Fallback succeeded via helper.get_mps_and_keys2")
                            else:
                                print("⚠️ Fallback returned nothing. Using original URL")
                                keys_string = ""
                        except Exception as e_fallback:
                            print(f"Fallback error: API FALLBACK")
                            keys_string = ""

                except Exception as e_api:
                    # API failed — attempt helper fallback before giving up
                    await m.reply_text(f" API failed: — attempting fallback...")
                    try:
                        res = helper.get_mps_and_keys2(url_norm)
                        if res:
                            mpd, keys = res
                            url = mpd
                            keys_string = " ".join([f"--key {k}" for k in keys])
                            print("🔁 Fallback succeeded via helper.get_mps_and_keys2")
                        else:
                            print("⚠️ Fallback returned nothing. Using original URL")
                            keys_string = ""
                    except Exception as e_fallback:
                        print(f"Fallback error: {e_fallback}")
                        keys_string = ""
            elif 'videos.classplusapp' in url or "tencdn.classplusapp" in url or "webvideos.classplusapp.com" in url:
                # call unified API as well
                try:
                    url_norm = url
                    api_url_call = f"https://shefu-api-final.vercel.app/shefu?url={url}@ITSGOLU_FORCE&user_id=8415922431"
                    resp = requests.get(api_url_call, timeout=30)
                    data = resp.json()
                    if isinstance(data, dict) and "url" in data:
                        url = data.get('url')
                        keys_string = ""
                    elif isinstance(data, dict) and "MPD" in data and "KEYS" in data:
                        mpd = data.get('MPD')
                        keys = data.get('KEYS', [])
                        url = mpd
                        keys_string = " ".join([f"--key {k}" for k in keys])
                except Exception:
                    # leave url as-is
                    keys_string = ""
            elif "childId" in url and "parentId" in url:
                url = f"https://anonymouspwplayer-25261acd1521.herokuapp.com/pw?url={url}&token={raw_text4}"
            
            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
                url = f"https://anonymouspwplayer-25261acd1521.herokuapp.com/pw?url={url}&token={raw_text4}"

            elif 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            elif "embed" in url:
                ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
           
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif ".m3u8.m3u8" in url or ".m3u8" in url:
            	cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
               cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:
                cc = f"**╭━━━━━ INFO ━━━━━╮**\n💫 **Video ID:** `{str(count).zfill(3)}`\n**╰━━━━━━━━━━━━━━╯**\n\n📁 **Title:** `{name1} ({res}) lucifer.mkv`\n📚 **Course:** `{b_name}`\n\n⚡ **Downloaded By:** {CR}"
                cc1 = f"<blockquote>╭━━━━━ INFO ━━━━━╮\n💫 <b>File ID:</b> <b>{str(count).zfill(3)}</b>\n╰━━━━━━━━━━━━━━╯\n\n📁 <b>Title:</b> <b>{name1} lucifer.pdf</b>\n📚 <b>Course:</b> <b>{b_name}</b>\n\n⚡ **Downloaded By:** {CR}</blockquote>"
                cczip = f"**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n📁 **Title:** `{name1}.zip`\n📚 **Course:** `{b_name}`\n\n⚡ **Extracted By:** {CR}"
                ccimg = f"**╭━━━━ IMAGE ━━━━╮**\n💫 **Image ID:** `{str(count).zfill(3)}`\n**╰━━━━━━━━━━━━━━╯**\n\n📁 **Title:** `{name1} lucifer.JPG`\n📚 **Course:** `{b_name}`\n\n⚡ **Downloaded By:** {CR}"
                ccm = f"**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n🎵 **Title:** `{name1}.mp3`\n📚 **Course:** `{b_name}`\n\n⚡ **Extracted By:** {CR}"
                cchtml = f"**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n🌐 **Title:** `{name1}.html`\n📚 **Course:** `{b_name}`\n\n⚡ **Extracted By:** {CR}"
    
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                        count += 1
                        os.remove(ka)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue    

                elif ".pdf" in url:
                    if "cwmediabkt99" in url:
                        max_retries = 15  # Define the maximum number of retries
                        retry_delay = 4  # Delay between retries in seconds
                        success = False  # To track whether the download was successful
                        failure_msgs = []  # To keep track of failure messages

                        for attempt in range(max_retries):
                            try:
                                await asyncio.sleep(retry_delay)
                                url = url.replace(" ", "%20")
                                scraper = cloudscraper.create_scraper()
                                response = scraper.get(url)

                                if response.status_code == 200:
                                    with open(f'{name}.pdf', 'wb') as file:
                                        file.write(response.content)
                                    await asyncio.sleep(retry_delay)  # Optional, to prevent spamming
                                    copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                                    count += 1
                                    os.remove(f'{name}.pdf')
                                    success = True
                                    break  # Exit the retry loop if successful
                                else:
                                    failure_msg = await m.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {response.status_code} {response.reason}")
                                    failure_msgs.append(failure_msg)

                            except Exception as e:
                                failure_msg = await m.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                                failure_msgs.append(failure_msg)
                                await asyncio.sleep(retry_delay)
                                continue  # Retry the next attempt if an exception occurs

                        # Delete all failure messages if the PDF is successfully downloaded
                        for msg in failure_msgs:
                            await msg.delete()

                        if not success:
                            # Send the final failure message if all retries fail
                            await m.reply_text(f"Failed to download PDF after {max_retries} attempts.\n⚠️**Downloading Failed**⚠️\n**Name** =>> {str(count).zfill(3)} {name1}\n**Url** =>> {link0}", disable_web_page_preview)

                    else:
                        try:
                            cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                            download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                            os.system(download_cmd)
                            copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                            count += 1
                            os.remove(f'{name}.pdf')
                        except FloodWait as e:
                            await m.reply_text(str(e))
                            time.sleep(e.x)
                            continue    

                elif ".ws" in url and url.endswith(".ws"):
                    try:
                        await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}", f"{name}.html")
                        time.sleep(1)
                        await bot.send_document(chat_id=m.chat.id, document=f"{name}.html", caption=cchtml)
                        os.remove(f'{name}.html')
                        count += 1
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue    
                        
                elif any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    try:
                        ext = url.split('.')[-1].split("?")[0]
                        filename = f"{name}.{ext}"

                        async with httpx.AsyncClient() as client:
                            r = await client.get(url)
                            if r.status_code == 200:
                                with open(filename, "wb") as f:
                                    f.write(r.content)
                            else:
                                await m.reply_text("❌ Failed to download image.")
                                return

                        if ext == "webp":
                            from PIL import Image
                            img = Image.open(filename).convert("RGB")
                            jpg_file = f"{name}.jpg"
                            img.save(jpg_file, "JPEG")
                            os.remove(filename)
                            filename = jpg_file

                        copy = await bot.send_photo(chat_id=m.chat.id, photo=filename, caption=ccimg)
                        count += 1
                        os.remove(filename)

                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        continue
                    except Exception as e:
                        await m.reply_text(f"⚠️ Error: {e}")



                elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                    try:
                        ext = url.split('.')[-1]
                        cmd = f'yt-dlp -o "{name}.{ext}" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.{ext}', caption=ccm)
                        count += 1
                        os.remove(f'{name}.{ext}')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        continue    

                    
                elif 'encrypted.m' in url:
                    res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                    if res_file:
                        await helper.send_vid(bot, m, cc, res_file, name)
                        count += 1
                    continue
                
                elif 'drmcdni' in url or 'drm/wv' in url or 'drm/common' in url:
                    res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                    if res_file:
                        await helper.send_vid(bot, m, cc, res_file, name)
                        count += 1    
                    continue
                
                else:
                    res_file = await helper.download_video(url, cmd, name)
                    if res_file:
                        await helper.send_vid(bot, m, cc, res_file, name)
                        count += 1
                    continue
   

    except Exception as e:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        await m.reply_text(e)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
    await m.reply_text("**Sᴜᴄᴄᴇsғᴜʟʟʏ Dᴏᴡɴʟᴏᴀᴅᴇᴅ Aʟʟ Lᴇᴄᴛᴜʀᴇs SIR 👿🚀**")               
                 
bot.run()
