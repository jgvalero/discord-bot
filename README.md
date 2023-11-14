# discord-bot
Very simple discord bot!
## Setup
### Create a virtual environment
It is recommended to create a virtual environment.
```bash
cd discord-bot
python3 -m venv bot-env
```
Activate the virtual environment.
```bash
source bot-env/bin/activate
```
Note: To exit the virtual environment, type `deactivate`.

### Install necessary packages
Install FFmpeg. On Ubuntu/Debian it can be installed using:
```bash
sudo apt install ffmpeg
```
With the virtual environment activated, install the required packages from the ```requirements.txt``` file.
```bash
pip install -r requirements.txt
```

### Create configuration
Rename `example_config.json` to `config.json` or create a new file and paste the example config into it.  
Acquire your tokens from Discord and Genius and paste them respectively.

## Run the Program
To run the program, make sure the virtual environment is activated and type `python3 main.py`.

### Optional configurations
You can make `blacklisted_words.txt` in the `data` directory that contains blacklisted words for your server.