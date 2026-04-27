import subprocess
import json
import re
import logging
import os
from typing import Optional, Tuple, List
from urllib.parse import urlparse

# Cookie file directory
COOKIE_DIR = "/app/cookies"

# Domain alias mapping: short domain -> primary cookie file domain
DOMAIN_ALIASES = {
    # Twitter/X
    'x.com': 'x.com',
    'twitter.com': 'x.com',
    't.co': 'x.com',
    # Instagram
    'instagram.com': 'instagram.com',
    'instagr.am': 'instagram.com',
    # Facebook
    'facebook.com': 'facebook.com',
    'fb.com': 'facebook.com',
    'fb.watch': 'facebook.com',
    # Bilibili
    'bilibili.com': 'bilibili.com',
    'bilibilibili.com': 'bilibili.com',
    'b23.tv': 'bilibili.com',
    # Douyin
    'douyin.com': 'douyin.com',
    # YouTube (for age-restricted content)
    'youtube.com': 'youtube.com',
    'youtu.be': 'youtube.com',
    # Weibo
    'weibo.com': 'weibo.com',
    'weibo.cn': 'weibo.com',
    't.cn': 'weibo.com',
}

def get_cookie_file(url: str) -> Optional[str]:
    """
    Find cookie file for a URL.
    Checks domain aliases and returns path to cookie file if exists.

    Args:
        url: The URL to find cookie for

    Returns:
        Path to cookie file if exists, None otherwise
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]

        # Remove 'www.' prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check direct domain match
        cookie_name = f"{domain}.txt"
        cookie_path = os.path.join(COOKIE_DIR, cookie_name)
        if os.path.exists(cookie_path):
            logging.info(f"Found cookie file for {domain}: {cookie_path}")
            return cookie_path

        # Check aliases
        for alias, primary in DOMAIN_ALIASES.items():
            if domain == alias or domain.endswith(f'.{alias}'):
                cookie_name = f"{primary}.txt"
                cookie_path = os.path.join(COOKIE_DIR, cookie_name)
                if os.path.exists(cookie_path):
                    logging.info(f"Found cookie file for {domain} via alias {alias}: {cookie_path}")
                    return cookie_path
                break

        logging.info(f"No cookie file found for {domain}")
        return None

    except Exception as e:
        logging.error(f"Error finding cookie file for {url}: {e}")
        return None
    """
    Check if yt-dlp supports this URL and get title + best m3u8 URL.

    Returns:
        (is_supported, title, m3u8_url)
    """
    try:
        # Use yt-dlp to get video info (dry run, don't download)
        cmd = [
            "python3", "-m", "yt_dlp",
            "--dump-json",
            "--no-download",
            "--no-warnings",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            logging.info(f"yt-dlp not supported for {url}: {result.stderr}")
            return (False, None, None)

        info = json.loads(result.stdout)

        title = info.get('title', 'Unknown')
        title = re.sub(r'[^\w\s\-\(\)\[\]]', '', title)[:100]  # Clean title

        # Try to get direct URL first (for sites that give direct m3u8)
        formats = info.get('formats', [])

        # Find m3u8 format
        m3u8_url = None
        for fmt in formats:
            url_value = fmt.get('url', '')
            ext = fmt.get('ext', '')
            format_id = fmt.get('format_id', '')
            tbr = fmt.get('tbr', 0)

            # Look for m3u8 URLs or direct stream URLs
            if '.m3u8' in url_value or ext == 'm3u8' or 'm3u8' in format_id:
                m3u8_url = url_value
                break

        # If no m3u8 found, check if it's a direct stream URL
        if not m3u8_url:
            for fmt in formats:
                url_value = fmt.get('url', '')
                if url_value and ('.mp4' in url_value or 'manifest' in url_value.lower()):
                    m3u8_url = url_value
                    break

        # If still no URL, maybe it's a webpage with embedded player
        # Return title but no m3u8 - caller should try N_m3u8DL-RE as fallback
        if not m3u8_url:
            logging.info(f"yt-dlp found title but no direct m3u8 URL for {url}")
            return (True, title, None)

        logging.info(f"yt-dlp supported: {url} -> {title}")
        return (True, title, m3u8_url)

    except subprocess.TimeoutExpired:
        logging.error(f"yt-dlp timeout for {url}")
        return (False, None, None)
    except json.JSONDecodeError as e:
        logging.error(f"yt-dlp JSON parse error for {url}: {e}")
        return (False, None, None)
    except Exception as e:
        logging.error(f"yt-dlp error for {url}: {e}")
        return (False, None, None)


def find_m3u8_in_text(text: str) -> List[str]:
    """Find m3u8 URLs in any text (HTML, JS, etc)."""
    pattern = r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*'
    matches = re.findall(pattern, text)
    return list(set(matches))


def extract_title_from_html(html: str) -> str:
    """Extract page title from HTML."""
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()
    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if og_title:
        return og_title.group(1).strip()
    return "Unknown"
