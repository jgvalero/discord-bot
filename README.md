# discord-bot

Simple Discord bot using discord.py!

## Setup

### Create a virtual environment

It is recommended to create a virtual environment.

```bash
cd discord-bot
python3 -m venv .venv
```

Activate the virtual environment.

```bash
source .venv/bin/activate
```

Note: To exit the virtual environment, type `deactivate`.

### Install necessary packages

Install FFmpeg. On Ubuntu/Debian it can be installed using:

```bash
sudo apt install ffmpeg
```

With the virtual environment activated, install the required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### Create configuration

Create a file with the name `.env`
Define your tokens in the `.env` file (Make sure to replace the example values)

```env
DISCORD_TOKEN = IAMADISCORDTOKEN
GUILD_ID = IAMAGUILDID

# Optional
GENIUS_TOKEN = IAMAGENIUSTOKEN
TTS_MONSTER_TOKEN = IAMATTSMONSTERTOKEN
```

## Run the Program

To run the program, make sure the virtual environment is activated and type `python3 main.py`.

### Optional configurations

Check out `config.toml` to configure the bot to your liking!
