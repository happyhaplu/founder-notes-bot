import re
import json
import logging
import subprocess
import tempfile
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_valid_youtube_url(url: str) -> bool:
    """Validate if the URL is a YouTube link."""
    youtube_domains = ["youtube.com", "youtu.be", "www.youtube.com", "m.youtube.com"]
    return any(domain in url.lower() for domain in youtube_domains)


def get_transcript_via_api(video_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch transcript using youtube-transcript-api v1.x."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        fetcher = YouTubeTranscriptApi()
        transcript_list = fetcher.list(video_id)

        # Pick English first, then any available
        chosen = None
        for t in transcript_list:
            if t.language_code.startswith("en"):
                chosen = t
                break
        if not chosen:
            for t in transcript_list:
                chosen = t
                break

        if not chosen:
            return None, "No transcripts available for this video"

        data = chosen.fetch()
        text = " ".join(s.text.strip() for s in data if s.text.strip())

        if len(text) > 80000:
            text = text[:80000]

        logger.info(f"[API] Transcript fetched: {len(text)} chars ({chosen.language})")
        return text, None

    except Exception as e:
        logger.warning(f"[API] Transcript failed: {e}")
        return None, str(e)


def get_transcript_via_ytdlp(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Use yt-dlp to download auto-generated subtitles as transcript."""
    try:
        import sys
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--skip-download",
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--output", os.path.join(tmpdir, "sub"),
                url
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            # Find the downloaded .vtt file
            vtt_file = None
            for f in os.listdir(tmpdir):
                if f.endswith(".vtt"):
                    vtt_file = os.path.join(tmpdir, f)
                    break

            if not vtt_file:
                logger.warning(f"[yt-dlp] No subtitle file found. stderr: {result.stderr[:200]}")
                return None, "No subtitles found via yt-dlp"

            with open(vtt_file, "r", encoding="utf-8") as f:
                raw = f.read()

            text = parse_vtt(raw)
            if not text.strip():
                return None, "Subtitle file was empty"

            logger.info(f"[yt-dlp] Transcript fetched: {len(text)} chars")
            return text, None

    except subprocess.TimeoutExpired:
        return None, "yt-dlp timed out"
    except Exception as e:
        logger.warning(f"[yt-dlp] Failed: {e}")
        return None, str(e)


def parse_vtt(vtt_text: str) -> str:
    """Parse WebVTT subtitle file into plain text, removing duplicates."""
    lines = vtt_text.splitlines()
    seen = set()
    result = []
    for line in lines:
        line = line.strip()
        # Skip headers, timestamps, and empty lines
        if (not line
                or line.startswith("WEBVTT")
                or line.startswith("NOTE")
                or "-->" in line
                or re.match(r"^\d+$", line)
                or re.match(r"^[\d:.,\s]+-->", line)):
            continue
        # Remove VTT tags like <c>, </c>, <00:00:01.000>
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line and line not in seen:
            seen.add(line)
            result.append(line)

    text = " ".join(result)
    if len(text) > 80000:
        text = text[:80000]
    return text


def process_youtube_url(url: str) -> dict:
    """
    Process a YouTube URL — validate, extract video ID, get transcript.
    Returns dict: valid, video_id, transcript, transcript_error, url
    """
    result = {
        "valid": False,
        "video_id": None,
        "transcript": None,
        "transcript_error": None,
        "url": url.strip(),
    }

    if not is_valid_youtube_url(url):
        result["transcript_error"] = "Not a valid YouTube URL"
        return result

    video_id = extract_video_id(url)
    if not video_id:
        result["transcript_error"] = "Could not extract video ID from URL"
        return result

    result["valid"] = True
    result["video_id"] = video_id

    # Method 1: youtube-transcript-api
    transcript, error = get_transcript_via_api(video_id)
    if transcript:
        result["transcript"] = transcript
        return result

    logger.info(f"Method 1 failed ({error}), trying yt-dlp...")

    # Method 2: yt-dlp subtitle download
    transcript, error = get_transcript_via_ytdlp(url)
    if transcript:
        result["transcript"] = transcript
        return result

    result["transcript_error"] = "Could not get transcript from this video. It may have subtitles disabled."
    logger.warning(f"Both transcript methods failed for {video_id}")
    return result

