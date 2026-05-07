import os
import re
import time
import logging
import requests
from prompts import FOUNDER_NOTES_PROMPT, TRANSCRIPT_SECTION_TEMPLATE

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openrouter/free"


def generate_founder_notes(url: str, transcript: str = None) -> str:
    """
    Generate founder notes using OpenRouter API.
    REQUIRES a real transcript — never generates without one.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")

    if not transcript or not transcript.strip():
        raise ValueError("no_transcript")

    transcript_section = TRANSCRIPT_SECTION_TEMPLATE.format(transcript=transcript)
    logger.info(f"Generating notes from transcript ({len(transcript)} chars)")

    prompt = FOUNDER_NOTES_PROMPT.format(
        url=url,
        transcript_section=transcript_section,
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/Founder_Note_bot",
        "X-Title": "Founder Notes Bot",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    # Retry up to 3 times on rate limit or timeout
    for attempt in range(3):
        try:
            logger.info(f"Calling OpenRouter (attempt {attempt + 1})...")
            response = requests.post(
                url=OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=120,
            )

            if response.status_code == 429:
                wait = 30 * (attempt + 1)
                logger.warning(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code != 200:
                raise ValueError(f"OpenRouter API error {response.status_code}: {response.text[:300]}")

            data = response.json()
            text = data["choices"][0]["message"]["content"]

            if not text or not text.strip():
                raise ValueError("OpenRouter returned an empty response")

            logger.info(f"Notes generated successfully ({len(text)} chars)")
            return text.strip()

        except requests.exceptions.Timeout:
            if attempt < 2:
                logger.warning(f"Request timed out, retrying...")
                time.sleep(10)
                continue
            raise ValueError("OpenRouter request timed out after 3 attempts")

        except ValueError:
            raise

        except Exception as e:
            raise ValueError(f"Failed to generate notes: {str(e)}")

    raise ValueError("OpenRouter: all retry attempts exhausted")


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """
    Split a long message into chunks for Telegram (4096 char limit).
    Splits on section dividers to keep formatting clean.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sections = text.split(divider)

    current_chunk = ""
    for i, section in enumerate(sections):
        separator = divider if i < len(sections) - 1 else ""
        candidate = current_chunk + section + separator

        if len(candidate) > max_length and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = section + separator
        else:
            current_chunk = candidate

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text[:max_length]]

