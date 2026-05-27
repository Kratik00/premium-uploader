import os
import re
import time
import mmap
import datetime
import json
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures
from math import ceil
from utils import progress_bar
from pyrogram import Client, filters
from pyrogram.types import Message
from io import BytesIO
from pathlib import Path  
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
from requests.exceptions import RequestException



# Same AES Key aur IV jo encryption ke liye use kiya tha
KEY = b'^#^#&@*HDU@&@*()'   
IV = b'^@%#&*NSHUE&$*#)'   

# Decryption function
def dec_url(enc_url):
    enc_url = enc_url.replace("helper://", "")  # "helper://" prefix hatao
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted = unpad(cipher.decrypt(b64decode(enc_url)), AES.block_size)
    return decrypted.decode('utf-8')

# Function to split name & Encrypted URL properly
def split_name_enc_url(line):
    match = re.search(r"(helper://\S+)", line)  # Find `helper://` ke baad ka encrypted URL
    if match:
        name = line[:match.start()].strip().rstrip(":")  # Encrypted URL se pehle ka text
        enc_url = match.group(1).strip()  # Sirf Encrypted URL
        return name, enc_url
    return line.strip(), None  # Agar encrypted URL nahi mila, to pura line name maan lo

def get_mps_and_keys2(api_url):
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raises exception for 4xx/5xx status codes
        response_json = response.json()
        mpd = response_json.get('mpd_url')
        keys = response_json.get('keys')
        return mpd, keys
    except RequestException as e:
        print(f"Request failed: {e}")
        return None, None
    except ValueError as e:
        print(f"JSON decode error: {e}")
        return None, None

def get_m3u8(session, url):

    try:

        if "vimeo.com" not in url:
            return url

        headers = {
            "Referer": "https://www.cdsjourney.com",
            "User-Agent": "Mozilla/5.0"
        }

        # ================= GET VIDEO ID =================

        video_id = None

        # review page fallback
        if "vimeo.com/reviews/" in url:

            r = session.get(
                url,
                headers=headers,
                timeout=20
            )

            page = r.text

            found = re.search(
                r'player\.vimeo\.com/video/(\d+)',
                page
            )

            if found:
                video_id = found.group(1)

        else:

            found = re.search(
                r'vimeo\.com/(?:video/)?(\d+)',
                url
            )

            if found:
                video_id = found.group(1)

        if not video_id:
            return url

        print(f"[+] VIDEO ID: {video_id}")

        # ================= OPEN PLAYER HTML =================

        player_url = (
            f"https://player.vimeo.com/video/{video_id}"
        )

        r = session.get(
            player_url,
            headers=headers,
            timeout=20
        )

        html_data = r.text

        # ================= PARSE playerConfig =================

        start = html_data.find(
            "window.playerConfig ="
        )

        if start == -1:

            print("[-] playerConfig missing")

            return url

        start = html_data.find("{", start)

        brace = 0
        end = None

        for i in range(start, len(html_data)):

            if html_data[i] == "{":
                brace += 1

            elif html_data[i] == "}":

                brace -= 1

                if brace == 0:

                    end = i + 1
                    break

        if not end:
            return url

        config_json = html_data[start:end]

        data = json.loads(config_json)

        # ================= GET HLS =================

        hls = (
            data["request"]
            ["files"]
            ["hls"]
            ["cdns"]
        )

        for cdn, info in hls.items():

            link = info.get("url")

            if link:

                print(
                    f"[+] M3U8 FOUND ({cdn})"
                )

                return link

        return url

    except Exception as e:

        print(
            f"M3U8 ERROR: {e}"
        )

        return url


# Function to decrypt file URLs
def decrypt_file_txt(input_file):
    output_file = "decrypted_" + input_file  # Output file ka naam

    # Ensure the directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            name, enc_url = split_name_enc_url(line)  # Sahi tarike se name aur encrypted URL split karo
            if enc_url:
                dec = dec_url(enc_url)  # Decrypt URL
                out.write(f"{name}: {dec}\n")  # Ek hi `:` likho
            else:
                out.write(line.strip() + "\n")  # Agar encrypted URL nahi mila to line jaisa hai waisa likho

    return output_file   # Decrypted file ka naam return karega
   
def duration(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

#def get_mps_and_keys(api_url):
    #response = requests.get(api_url)
   # response_json = response.json()
   # mpd = response_json.get('MPD')
   # keys = response_json.get('KEYS')
   # return mpd, keys
   
def exec(cmd):
        process = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output = process.stdout.decode()
        print(output)
        return output
        #err = process.stdout.decode()
def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec,cmds)
async def aio(url,name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k


async def download(url,name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka

async def pdf_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name   
   

async def is_live_stream(url):
    try:
        proc = await asyncio.create_subprocess_shell(
            f'yt-dlp --print is_live "{url}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        stdout, _ = await proc.communicate()
        return stdout.decode().strip() == "True"

    except:
        return False
def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info


def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    
                    # temp.update(f'{i[2]}')
                    # new_info.append((i[2], i[0]))
                    #  mp4,mkv etc ==== f"({i[1]})" 
                    
                    new_info.update({f'{i[2]}':f'{i[0]}'})

            except:
                pass
    return new_info


async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        cmd1 = f'yt-dlp -f "bv[height<={quality}]+ba/b" -o "{output_path}/file.%(ext)s" --allow-unplayable-format --no-check-certificate --external-downloader aria2c "{mpd_url}"'
        print(f"Running command: {cmd1}")
        os.system(cmd1)
        
        avDir = list(output_path.iterdir())
        print(f"Downloaded files: {avDir}")
        print("Decrypting")

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                cmd2 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/video.mp4"'
                print(f"Running command: {cmd2}")
                os.system(cmd2)
                if (output_path / "video.mp4").exists():
                    video_decrypted = True
                data.unlink()
            elif data.suffix == ".m4a" and not audio_decrypted:
                cmd3 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/audio.m4a"'
                print(f"Running command: {cmd3}")
                os.system(cmd3)
                if (output_path / "audio.m4a").exists():
                    audio_decrypted = True
                data.unlink()

        if not video_decrypted or not audio_decrypted:
            raise FileNotFoundError("Decryption failed: video or audio file not found.")

        cmd4 = f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" -c copy "{output_path}/{output_name}.mp4"'
        print(f"Running command: {cmd4}")
        os.system(cmd4)
        if (output_path / "video.mp4").exists():
            (output_path / "video.mp4").unlink()
        if (output_path / "audio.m4a").exists():
            (output_path / "audio.m4a").unlink()
        
        filename = output_path / f"{output_name}.mp4"

        if not filename.exists():
            raise FileNotFoundError("Merged video file not found.")

        cmd5 = f'ffmpeg -i "{filename}" 2>&1 | grep "Duration"'
        duration_info = os.popen(cmd5).read()
        print(f"Duration info: {duration_info}")

        return str(filename)

    except Exception as e:
        print(f"Error during decryption and merging: {str(e)}")
        raise

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'

    

def old_download(url, file_name, chunk_size = 1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"


async def download_video(url,cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    global failed_counter
    print(download_cmd)
    logging.info(download_cmd)
    k = subprocess.run(download_cmd, shell=True)
    if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
        failed_counter += 1
        await asyncio.sleep(5)
        await download_video(url, cmd, name)
    failed_counter = 0
    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        name = name.split(".")[0]
        if os.path.isfile(f"{name}.mkv"):
            return f"{name}.mkv"
        elif os.path.isfile(f"{name}.mp4"):
            return f"{name}.mp4"
        elif os.path.isfile(f"{name}.mp4.webm"):
            return f"{name}.mp4.webm"

        return name
    except FileNotFoundError as exc:
        return os.path.isfile.splitext[0] + "." + "mp4"

# async def send_doc(bot: Client, m: Message, file_path, caption):

#     try:
#         sent = await m.reply_document(
#             file_path,
#             caption=caption
#         )

#     finally:
#         if os.path.exists(file_path):
#             os.remove(file_path)

#     return sent

# async def send_doc(
#     bot,
#     m,
#     file_path,
#     caption,
#     channel_id=None,
#     topic_id=None
# ):

#     try:

#         if channel_id:
#             kwargs = dict(
#                 chat_id=channel_id,
#                 document=file_path,
#                 caption=caption
#             )

#             if topic_id:
#                 kwargs["message_thread_id"] = topic_id

#             try:
#                 sent = await bot.send_document(**kwargs)

#             except TypeError:
#                 kwargs.pop("message_thread_id", None)
#                 sent = await bot.send_document(**kwargs)

#         else:
#             sent = await m.reply_document(
#                 file_path,
#                 caption=caption
#             )

#     finally:
#         if os.path.exists(file_path):
#             os.remove(file_path)

#     return sent

async def send_doc(bot: Client, m: Message, ka, cc1, channel_id, topic_id=None):

    thread_kwargs = {"message_thread_id": topic_id} if topic_id else {}

    # TELEGRAM FILE_ID SUPPORT
    if str(ka).startswith(("BAAC", "CAAC")):
        return await bot.send_document(
            chat_id=channel_id,
            document=ka,
            caption=cc1,
            **thread_kwargs
        )

    # LOCAL FILE SUPPORT
    try:
        sent = await bot.send_document(
            chat_id=channel_id,
            document=ka,
            caption=cc1,
            **thread_kwargs
        )

        await asyncio.sleep(1)

        return sent

    finally:
        if os.path.exists(ka):
            os.remove(ka)

def decrypt_file(file_path, key):  
    if not os.path.exists(file_path): 
        return False  

    with open(file_path, "r+b") as f:  
        num_bytes = min(28, os.path.getsize(file_path))  
        with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:  
            for i in range(num_bytes):  
                mmapped_file[i] ^= ord(key[i]) if i < len(key) else i 
    return True  

async def download_and_decrypt_video(url, cmd, name, key):  
    video_path = await download_video(url, cmd, name)  
    
    if video_path:  
        decrypted = decrypt_file(video_path, key)  
        if decrypted:  
            print(f"File {video_path} decrypted successfully.")  
            return video_path  
        else:  
            print(f"Failed to decrypt {video_path}.")  
            return None  

MAX_FILE_SIZE_BYTES = 2000 * 1024 * 1024

async def split_video(filename):
    """Split a video into parts of ~1999 MB each using ffmpeg segment muxer."""
    base, ext = os.path.splitext(filename)
    pattern = f"{base}_part%03d{ext}"

    # Calculate how many parts we need based on file size
    file_size = os.path.getsize(filename)
    part_size = 1999 * 1024 * 1024  # 1999 MB in bytes
    num_parts = ceil(file_size / part_size)

    # Get total duration using ffprobe
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    total_duration = float(result.stdout.strip() or 0)

    # Calculate duration per part proportionally
    part_duration_secs = int(total_duration / num_parts) if num_parts > 1 else int(total_duration)

    cmd = (
        f'ffmpeg -i "{filename}" -c copy -map 0 '
        f'-segment_time {part_duration_secs} -f segment -reset_timestamps 1 '
        f'"{pattern}" -y'
    )
    subprocess.run(cmd, shell=True)

    # Collect generated part files in order
    dir_name = os.path.dirname(filename) or "."
    parts = sorted([
        f for f in os.listdir(dir_name)
        if os.path.basename(f).startswith(os.path.basename(base) + "_part") and f.endswith(ext)
    ])
    return [os.path.join(dir_name, p) for p in parts]
async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, channel_id, topic_id=None):

    thread_kwargs = {"message_thread_id": topic_id} if topic_id else {}

    # TELEGRAM FILE_ID SUPPORT
    if str(filename).startswith(("BAAC", "CAAC")):

        try:
            return await bot.send_video(
                channel_id,
                filename,
                caption=cc,
                supports_streaming=True,
                **thread_kwargs
            )

        except Exception:
            return await bot.send_document(
                channel_id,
                filename,
                caption=cc,
                **thread_kwargs
            )

    # LOCAL FILE LOGIC
    subprocess.run(
        f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"',
        shell=True
    )

    thumbnail = f"{filename}.jpg"

    dur = int(duration(filename))
    file_size = os.path.getsize(filename)

    try:

        if file_size > MAX_FILE_SIZE_BYTES:

            split_msg = await m.reply_text(
                f"⚠️ File size is **{file_size // (1024*1024)} MB**, splitting..."
            )

            parts = await split_video(filename)

            await split_msg.delete()

            if not parts:
                parts = [filename]

            for idx, part_file in enumerate(parts, start=1):

                part_caption = f"{cc}\n\n📦 Part {idx}/{len(parts)}"

                try:
                    await bot.send_video(
                        channel_id,
                        part_file,
                        caption=part_caption,
                        supports_streaming=True,
                        thumb=thumbnail,
                        duration=int(duration(part_file)),
                        **thread_kwargs
                    )

                except Exception:

                    await bot.send_document(
                        channel_id,
                        part_file,
                        caption=part_caption,
                        **thread_kwargs
                    )

                if part_file != filename and os.path.exists(part_file):
                    os.remove(part_file)

        else:

            try:
                return await bot.send_video(
                    channel_id,
                    filename,
                    caption=cc,
                    supports_streaming=True,
                    thumb=thumbnail,
                    duration=dur,
                    **thread_kwargs
                )

            except Exception:

                return await bot.send_document(
                    channel_id,
                    filename,
                    caption=cc,
                    **thread_kwargs
                )

    finally:

        if os.path.exists(filename):
            os.remove(filename)

        if os.path.exists(thumbnail):
            os.remove(thumbnail)
