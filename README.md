# Python_Music_Bot_Discord
Discord Music Bot made using python

## Status
The Bot is correctly working!!

## Using the Bot

### Add token to .env file
Content in .env file should look like
```ini
[Discord]
TOKEN={{ Discord token }}

[Spotify]
CLIENT_ID={{ Spotify Client ID }}
CLIENT_SECRET={{ Spotify Client Secret }}
```

### Setup a python virtual environment
```bash
python -m venv bot
```
Activate the virtual environment.
Install the requirements from `requirements.txt`

### Run the script
Run the script and start the music in you're discord channels!!

## Contributing

Make sure to install all the modules in `pre-commit-req.txt` and run the pre-commits before any request.
