import json
import os
import sys

import requests
from dotenv import load_dotenv

if not load_dotenv():
    print("Could not locate .env!")
    sys.exit(1)
tts_monster_token = os.getenv("TTS_MONSTER")

if os.path.exists("data/voices.json"):
    with open("data/voices.json", "r") as f:
        voice_id = json.load(f)


def get_url(message: str) -> str:
    headers = {"Authorization": tts_monster_token}
    payload = {"voice_id": message["voice_id"], "message": message["message"]}
    r = requests.post(
        "https://api.console.tts.monster/generate", headers=headers, json=payload
    )
    text = json.loads(r.text)
    return text["url"]


def parse_input(input: str):
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

            new_speaker = part.split(":")[0]
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


def generate_tts(input: str):
    messages = parse_input(input)

    if get_count(messages) > 100:
        return None

    urls = []

    for message in messages:
        urls.append(get_url(message))

    return urls


def get_voices():
    return ", ".join(voice_id.keys())


def get_count(messages):
    return sum(len(item["message"]) for item in messages)
