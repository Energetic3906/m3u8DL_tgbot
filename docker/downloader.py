import os
import shutil
import logging
import subprocess
import pathlib
import uuid
import time
import random
import tempfile
import fakeredis
import json
from pathlib import Path
from pyrogram.types import Message
from pyrogram import Client, filters, types, enums
from io import StringIO
from tqdm import tqdm


def download_and_upload_video(user_client, client, message, user_message, base_save_dir, custom_title=None, display_url=None, is_premium=False):
    chat_id = message.chat.id

    # Use display_url for caption if provided, otherwise use user_message
    caption_url = display_url if display_url else user_message

    # File size limits in bytes
    REGULAR_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB
    PREMIUM_LIMIT = 4 * 1024 * 1024 * 1024   # 4GB
    size_limit = PREMIUM_LIMIT if is_premium else REGULAR_LIMIT

    try:
        save_dir = tempfile.mkdtemp(dir=base_save_dir)

        # Try yt-dlp first, fallback to N_m3u8DL-RE
        video_paths = None
        error_msg = None

        # Try yt-dlp first
        try:
            video_paths = ytdlp_download(user_message, save_dir, custom_title)
            logging.info(f"Downloaded using yt-dlp: {user_message}")
        except Exception as e:
            logging.warning(f"yt-dlp failed, trying N_m3u8DL-RE: {e}")
            error_msg = str(e)

        # Fallback to N_m3u8DL-RE if yt-dlp didn't work
        if not video_paths:
            try:
                video_paths = ytdl_download(user_message, save_dir, custom_title)
                logging.info(f"Downloaded using N_m3u8DL-RE: {user_message}")
            except Exception as e:
                raise Exception(f"Both yt-dlp and N_m3u8DL-RE failed.\n\nyt-dlp error: {error_msg}\n\nN_m3u8DL-RE error: {e}")

        for video_path in video_paths:
            file_size = video_path.stat().st_size
            logging.info(f"File size: {file_size / (1024*1024):.2f}MB, limit: {size_limit / (1024*1024*1024):.1f}GB")

            # Compress if file exceeds size limit
            if file_size > size_limit:
                logging.info(f"File exceeds limit, compressing...")
                video_path = compress_video(video_path, size_limit, is_premium)

            video_path_str = str(video_path)
            print("video_paths: ", video_path_str)
            cap, meta = gen_cap(message, caption_url, video_path_str, custom_title)
            video_path_str = str(video_path)
            print("video_paths: ", video_path_str)
            cap, meta = gen_cap(message, caption_url, video_path_str, custom_title)
            print("cap: ", cap)
            print("meta: ", meta)
            user_client.send_video(
                chat_id,
                video_path_str,
                caption=cap,
                progress=upload_hook,
                progress_args=(message,),
                **meta
            )

        message.edit_text(f"Download success!✅✅✅")

        # Cleanup
        for item in os.listdir(save_dir):
            item_path = os.path.join(save_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                logging.error(f"Failed to delete {item_path}: {str(e)}")

        try:
            os.rmdir(save_dir)
        except OSError as e:
            if e.errno == 39:  # ENOTEMPTY
                pass
            else:
                raise

    except Exception as e:
        client.send_message(chat_id, f"Download failed: {str(e)}")


def ytdlp_download(url: str, savedir: str, custom_title: str = None):
    """Download video using yt-dlp."""
    tempdir = "/tmp/m3u8D/downloading"
    os.makedirs(tempdir, exist_ok=True)

    # Build filename
    if custom_title:
        # Clean title for filesystem
        safe_title = "".join(c for c in custom_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50] if len(safe_title) > 50 else safe_title
        save_name = safe_title.replace(' ', '_') if safe_title else f"{uuid.uuid4().hex}"
    else:
        save_name = f"{uuid.uuid4().hex}"

    output_path = os.path.join(savedir, save_name)

    try:
        # Use yt-dlp to download - it handles m3u8 and many other formats
        cmd = [
            "python3", "-m", "yt_dlp",
            "-o", f"{output_path}.%(ext)s",
            "--no-playlist",
            "--no-warnings",
            url
        ]
        print(f"yt-dlp downloading: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise Exception(f"yt-dlp failed: {result.stderr}")

        # Find downloaded file
        video_paths = list(pathlib.Path(savedir).glob(f"{save_name}.*"))
        video_paths = [p for p in video_paths if p.suffix.lower() not in {'.part', '.ytdl'}]

        if not video_paths:
            raise Exception("yt-dlp downloaded but no file found")

        # Convert to MP4 if needed
        return convert_to_mp4(video_paths)

    except subprocess.TimeoutExpired:
        raise Exception("yt-dlp download timeout")
    except Exception as e:
        raise Exception(f"yt-dlp download failed: {e}")


def ytdl_download(url: str, savedir: str, custom_title: str = None):
    tempdir = "/tmp/m3u8D/downloading"
    os.makedirs(tempdir, exist_ok=True)

    # Generate save name
    if custom_title:
        safe_title = "".join(c for c in custom_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50] if len(safe_title) > 50 else safe_title
        save_name = safe_title.replace(' ', '_') if safe_title else f"{uuid.uuid4().hex}"
    else:
        save_name = f"{uuid.uuid4().hex}"

    try:
        download_command = [
            "./N_m3u8DL-RE",
            url,
            "--tmp-dir", tempdir,
            "--save-dir", savedir,
            "--save-name", save_name,
            "--auto-select"
        ]
        logging.info(f"N_m3u8DL-RE downloading: {url}")

        process = subprocess.Popen(
            download_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True
        )

        for line in process.stdout:
            line = line.strip()
            if line:
                logging.info(f"[N_m3u8DL-RE] {line}")

        process.wait()
        if process.returncode != 0:
            raise Exception(f"N_m3u8DL-RE exited with code {process.returncode}")

        video_paths = list(pathlib.Path(savedir).glob("*"))

        return convert_to_mp4(video_paths)

    except Exception as e:
        raise Exception(f"N_m3u8DL-RE download failed: {url} - {e}")


def convert_to_mp4(video_paths):
    """Convert non-MP4 video files to MP4."""
    skip_extensions = {'.srt', '.vtt', '.ass', '.ssa', '.sub', '.part', '.ytdl', '.tmp'}
    final_video_paths = []

    for video_path in video_paths:
        ext = video_path.suffix.lower()
        name = video_path.name.lower()

        # Skip subtitle and partial/temporary files
        if ext in skip_extensions or '.part' in name or '.ytdl' in name:
            print(f"[SKIP] Skipping: {video_path}")
            continue

        # Check if file is actually complete (not .part file without extension)
        if video_path.stat().st_size < 1000:  # Skip very small files (likely incomplete)
            print(f"[SKIP] Too small, likely incomplete: {video_path}")
            continue

        if ext == ".mp4":
            final_video_paths.append(video_path)
        else:
            new_file_path = video_path.with_suffix(".mp4")
            print(f"[CONVERT] {video_path} -> {new_file_path}")
            result = subprocess.run(
                ["ffmpeg", "-i", str(video_path), "-c:v", "copy", "-c:a", "copy", str(new_file_path)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"[ERROR] FFmpeg failed: {result.stderr}")
                raise Exception(f"FFmpeg conversion failed for {video_path}")
            video_path.unlink()
            final_video_paths.append(new_file_path)

    for video_path in final_video_paths:
        print(f"Download completed: {video_path}")
    return final_video_paths


def compress_video(video_path: Path, max_size_bytes: int, is_premium: bool):
    """
    Compress video to fit within max_size_bytes using FFmpeg.
    Calculates target bitrate based on duration and target size.
    """
    import math

    # Get video metadata
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", str(video_path)
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.warning(f"ffprobe failed for {video_path}, skipping compression")
        return video_path

    info = json.loads(result.stdout)
    duration_str = info.get("format", {}).get("duration", "0")
    try:
        duration = float(duration_str)
    except (ValueError, TypeError):
        duration = 0

    if duration <= 0:
        logging.warning(f"Could not get duration for {video_path}, skipping compression")
        return video_path

    # Target size with 10% buffer for container/metadata overhead
    target_size = max_size_bytes * 0.9

    # Audio bitrate (keep original audio)
    audio_bitrate = 128 * 1024  # 128kbps

    # Calculate video bitrate
    # target_size (bytes) = video_bitrate (bytes/s) * duration (s) + audio_bitrate * duration
    # video_bitrate = (target_size / duration) - audio_bitrate
    video_bitrate_bps = (target_size / duration) - audio_bitrate
    video_bitrate_kbps = math.floor(video_bitrate_bps / 1024)

    # Minimum bitrate check (don't go too low)
    min_bitrate_kbps = 500
    if video_bitrate_kbps < min_bitrate_kbps:
        logging.warning(f"Calculated bitrate too low ({video_bitrate_kbps}kbps), using minimum {min_bitrate_kbps}kbps")
        video_bitrate_kbps = min_bitrate_kbps

    logging.info(f"Compressing: duration={duration:.1f}s, target_size={target_size/(1024*1024):.1f}MB, video_bitrate={video_bitrate_kbps}kbps")

    # Create output path
    output_path = video_path.with_suffix(".compressed.mp4")

    # Compress with calculated bitrate
    compress_cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-c:v", "libx264", "-b:v", f"{video_bitrate_kbps}k",
        "-maxrate", f"{video_bitrate_kbps * 1.5}k", "-bufsize", f"{video_bitrate_kbps * 2}k",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    logging.info(f"Running: {' '.join(compress_cmd)}")

    result = subprocess.run(
        compress_cmd,
        capture_output=True,
        text=True,
        timeout=max(600, int(duration * 2))  # At least 10 min, or 2x duration
    )

    if result.returncode != 0:
        logging.error(f"Compression failed: {result.stderr}")
        # Try simpler compression (just CRF-based)
        logging.info("Trying simpler compression...")
        simple_cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-c:v", "libx264", "-crf", "28",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(simple_cmd, capture_output=True, text=True, timeout=max(600, int(duration * 2)))
        if result.returncode != 0:
            logging.error(f"Simple compression also failed: {result.stderr}")
            return video_path  # Return original if compression fails

    # Check if compressed file is within limit
    compressed_size = output_path.stat().st_size
    if compressed_size > max_size_bytes:
        logging.warning(f"Compressed file still too large: {compressed_size/(1024*1024):.1f}MB > {max_size_bytes/(1024*1024*1024):.1f}GB")
        # Try more aggressive compression
        video_bitrate_kbps = max(300, video_bitrate_kbps // 2)
        aggressive_cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-c:v", "libx264", "-b:v", f"{video_bitrate_kbps}k",
            "-maxrate", f"{video_bitrate_kbps * 1.5}k", "-bufsize", f"{video_bitrate_kbps * 2}k",
            "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        result = subprocess.run(aggressive_cmd, capture_output=True, text=True, timeout=max(600, int(duration * 2)))
        if result.returncode == 0:
            compressed_size = output_path.stat().st_size

    logging.info(f"Compression complete: {compressed_size/(1024*1024):.1f}MB (was {video_path.stat().st_size/(1024*1024):.1f}MB)")

    # Remove original, return compressed
    video_path.unlink()
    return output_path


def gen_cap(bm, url, video_path, custom_title=None):
    video_path = Path(video_path)
    chat_id = bm.chat.id
    user = bm.chat
    try:
        user_info = "@{}({})-{}".format(user.username or "N/A", user.first_name or "" + user.last_name or "", user.id)
    except Exception:
        user_info = ""

    if isinstance(video_path, pathlib.Path):
        meta = get_metadata(video_path)
        file_name = video_path.name
        file_size = sizeof_fmt(os.stat(video_path).st_size)
        print("size_instance: ", file_size)
    else:
        file_name = getattr(video_path, "file_name", "")
        file_size = sizeof_fmt(getattr(video_path, "file_size", (2 << 2) + ((2 << 2) + 1) + (2 << 5)))
        print("size_not_instance: ", file_size)
        meta = dict(
            width=getattr(video_path, "width", 0),
            height=getattr(video_path, "height", 0),
            duration=getattr(video_path, "duration", 0),
            thumb=getattr(video_path, "thumb", None),
        )

    # Use custom_title if provided, otherwise use filename
    if custom_title:
        display_name = custom_title
    else:
        display_name = os.path.splitext(file_name)[0]

    cap = f"{display_name}\n\n{url}\t"
    return cap, meta


def get_metadata(video_path):
    width, height, duration = 1280, 720, 0
    try:
        # Use ffprobe to get video metadata
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-select_streams", "v:0", "-show_streams", "-show_format", str(video_path)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)

        # Get dimensions
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width", 1280)
                height = stream.get("height", 720)
                break

        # Get duration
        format_info = info.get("format", {})
        duration = int(float(format_info.get("duration", 0) or 0))

    except Exception as e:
        logging.error(f"ffprobe error: {e}")

    # Generate thumbnail
    thumb = None
    try:
        thumb_path = pathlib.Path(video_path).parent.joinpath(f"{uuid.uuid4().hex}-thumbnail.png")
        thumb_cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-ss", "1", "-vframes", "1",
            "-vf", f"scale={width}:-1",
            str(thumb_path)
        ]
        result = subprocess.run(thumb_cmd, capture_output=True, text=True)
        if result.returncode == 0 and thumb_path.exists():
            thumb = thumb_path.as_posix()
        else:
            logging.warning(f"Thumbnail generation failed: {result.stderr}")
    except Exception as e:
        logging.error(f"Thumbnail error: {e}")

    return dict(height=height, width=width, duration=duration, thumb=thumb)


def sizeof_fmt(num: int, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def upload_hook(current, total, bot_msg):
    text = tqdm_progress("Uploading...", total, current)
    edit_text(bot_msg, text)


def tqdm_progress(desc, total, finished, speed="", eta=""):
    def more(title, initial):
        if initial:
            return "%s %s" % (title, initial)
        else:
            return ""

    f = StringIO()
    tqdm(
        total=total,
        initial=finished,
        file=f,
        ascii=False,
        unit_scale=True,
        ncols=30,
        bar_format="{l_bar}{bar} |{n_fmt}/{total_fmt} ",
    )
    raw_output = f.getvalue()
    tqdm_output = raw_output.split("|")
    progress = "`[%s]`" % tqdm_output[1]
    detail = tqdm_output[2].replace("[A", "")
    text = """
%s

%s
%s
%s
%s    """ % (desc, progress, detail, more("Speed:", speed), more("ETA:", eta))
    f.close()
    return text


r = fakeredis.FakeStrictRedis()


def edit_text(bot_msg, text: str):
    key = "%s-%s" % (bot_msg.chat.id, bot_msg.id)
    if not r.exists(key):
        time.sleep(random.random())
        r.set(key, "ok", ex=3)
        bot_msg.edit_text(text)


