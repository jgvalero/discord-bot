import asyncio
import functools
import json
import os
import sys
from typing import Any, Callable, Coroutine, Dict, List, Optional

import requests
import tomllib
from dotenv import load_dotenv

if not load_dotenv():
    print("Could not locate .env!")
    sys.exit(1)
tts_monster_token = os.getenv("TTS_MONSTER_TOKEN")

with open("config.toml", "rb") as f:
    config = tomllib.load(f)["tts"]
    voice_id = config["voice"]


def to_thread(func: Callable) -> Callable[..., Coroutine[Any, Any, Any]]:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


def get_url(message: Dict[str, str]) -> str:
    headers = {"Authorization": tts_monster_token}
    payload = {"voice_id": message["voice_id"], "message": message["message"]}
    r = requests.post(
        "https://api.console.tts.monster/generate", headers=headers, json=payload
    )
    text = json.loads(r.text)
    return text["url"]


def parse_input(input: str) -> List[Dict[str, str]]:
    messages = []
    parts = input.split(" ")

    current_speaker = None
    current_message = []

    for part in parts:
        if ":" in part:
            if current_speaker is not None:
                messages.append(
                    {
                        "name": current_speaker,
                        "voice_id": voice_id[current_speaker],
                        "message": " ".join(current_message).strip(),
                    }
                )

            new_speaker = part.split(":")[0].lower()
            if new_speaker in voice_id:
                current_speaker = new_speaker
                current_message = [part.split(":")[1]]
            else:
                current_message.append(part)
        else:
            current_message.append(part)

    if current_speaker is not None:
        messages.append(
            {
                "name": current_speaker,
                "voice_id": voice_id[current_speaker],
                "message": " ".join(current_message).strip(),
            }
        )

    return messages


@to_thread
def generate_tts(input: str) -> Optional[List[str]]:
    messages = parse_input(input)

    if get_count(messages) > 100:
        return None

    urls = []

    for message in messages:
        urls.append(get_url(message))

    return urls


def get_voices() -> str:
    return ", ".join(voice_id.keys())


def get_count(messages: List[Dict[str, str]]) -> int:
    return sum(len(item["message"]) for item in messages)
