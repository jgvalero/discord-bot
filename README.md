# discord-bot

Very simple discord bot!

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
```

## Run the Program

To run the program, make sure the virtual environment is activated and type `python3 main.py`.

### Optional configurations

You can make `blacklisted_words.txt` in the `data` directory that contains blacklisted words for your server. Check out the example!
You can make `example_trivia_questions.json` in the `data` directory that contains trivia questions for your server. Check out the example!
