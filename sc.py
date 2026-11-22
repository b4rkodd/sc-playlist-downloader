#!/usr/bin/env python3
"""
SoundCloud playlist downloader.

Usage:
    python sc_downloader.py                      # asks for the playlist link
    python sc_downloader.py <playlist-link>

Every run creates a new folder (sc1, sc2, sc3, ...) in
/storage/emulated/0/Download and downloads every track of the playlist into it.

On Termux, run `termux-setup-storage` once first so the script is allowed to
write to /storage/emulated/0/Download.

Requirements:
    pip install yt-dlp
    ffmpeg (optional, but needed to convert songs to MP3 and embed tags/cover art)
"""

import re
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

try:
    from yt_dlp import YoutubeDL
except ImportError:
    sys.exit("yt-dlp is not installed. Run:  pip install yt-dlp")

# All sc1, sc2, sc3... folders are created here.
BASE_DIR = Path("/storage/emulated/0/Download")


def next_folder() -> Path:
    """Return the first non-existing folder named sc1, sc2, sc3, ..."""
    existing = []
    for p in BASE_DIR.glob("sc*"):
        m = re.fullmatch(r"sc(\d+)", p.name)
        if m and p.is_dir():
            existing.append(int(m.group(1)))
    n = max(existing, default=0) + 1
    while (BASE_DIR / f"sc{n}").exists():
        n += 1
    return BASE_DIR / f"sc{n}"


def resolve_short_link(url: str) -> str:
    """Expand on.soundcloud.com short links to the full soundcloud.com URL."""
    host = urlparse(url).netloc.lower()
    if host != "on.soundcloud.com":
        return url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.geturl()
    except Exception as e:
        print(f"Could not expand short link ({e}), trying it as-is...")
        return url


def download(url: str) -> None:
    url = resolve_short_link(url.strip())

    if not BASE_DIR.is_dir():
        sys.exit(f"{BASE_DIR} was not found. On Termux, run `termux-setup-storage` "
                 "first and allow storage access, then try again.")

    folder = next_folder()
    folder.mkdir(parents=True)
    print(f"\nCreated folder: {folder}\n")

    has_ffmpeg = shutil.which("ffmpeg") is not None

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(folder / "%(playlist_index|)s%(playlist_index& - |)s%(title)s.%(ext)s"),
        "ignoreerrors": True,      # skip tracks that fail (private, geo-blocked, ...)
        "noplaylist": False,
        "restrictfilenames": False,
        "windowsfilenames": True,  # strip characters that are illegal on some filesystems
        "retries": 5,
        "quiet": False,
        "no_warnings": False,
    }

    if has_ffmpeg:
        opts["writethumbnail"] = True
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ]
    else:
        print("ffmpeg not found - songs will be saved in their original format "
              "(usually m4a/opus/mp3) without conversion.\n")

    with YoutubeDL(opts) as ydl:
        ydl.download([url])

    files = [p for p in folder.iterdir() if p.is_file()]
    print(f"\nDone. {len(files)} file(s) saved in {folder}")


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else input("Paste the SoundCloud playlist link: ")
    if not url.strip():
        sys.exit("No link provided.")
    download(url)


if __name__ == "__main__":
    main()
