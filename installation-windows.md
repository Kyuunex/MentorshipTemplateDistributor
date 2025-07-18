# Installation on Windows
### Requirements:
+ Git from https://git-scm.com/downloads
+ Python (version 3.10 minimum) from https://www.python.org/downloads/

### Intents
[Visit this page](https://discord.com/developers/applications/), locate your bot and enable 
- SERVER MEMBERS INTENT
- MESSAGE CONTENT INTENT

### Where is the bot's data folder
`C:\Users\username\AppData\Local\Kyuunex\MTD`  
If you are restoring a database backup, it goes into this folder.

### API keys and tokens
You need to either put them in the respective text files in the bot's data folder or 
supply them via environment variables. if you do both, env vars will be used  

| text file  | environment variables | where to get |
| ------------- | ------------- | ------------- |
| token.txt  | MTD_TOKEN  | [create a new app, make a bot acc](https://discord.com/developers/applications/) |

## Installation for production use
Head over to the Releases section, pick the latest release, 
and in its description you will see an installation command. 
Open the Terminal (PowerShell or CMD), paste that in and press enter.

To install the latest unstable version, type the following in the Terminal instead 
```bash
python3 -m pip install git+https://github.com/Kyuunex/MentorshipTemplateDistributor.git@master --upgrade
```

To run the bot, type `python3 -m mtd` in the Terminal

#### Startup with automatic restart
The purpose of this is to make the bot start automatically on boot, useful for example after a power outage.  
Make a `.bat` file with the following contents and put it into your startup folder.
```bat
@echo off
title MTD
:loop
python3 -m mtd
goto loop
pause
```

## Installation for debugging and development
```bash
git clone https://github.com/Kyuunex/MentorshipTemplateDistributor.git -b master MTD
cd MTD
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
./run_mtd.py
```
To install a modified version of the bot for production use, type `pip3 install . --upgrade` while in the same directory
