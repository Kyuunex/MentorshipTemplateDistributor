# Installation on Linux
NOTE: These instructions were written for debian bullseye. Since then, one thing changed and that is, externally-managed-environment.
# TODO: update this

### Requirements:
+ `git`
+ `python3` (version 3.10 minimum)

### Intents
[Visit this page](https://discord.com/developers/applications/), locate your bot and enable 
- SERVER MEMBERS INTENT
- MESSAGE CONTENT INTENT

### Where is the bot's data folder
`/home/username/.local/share/MTD`  
If you are restoring a database backup, it goes into this folder.

### API keys and tokens
You need to either put them in the respective text files in the bot's data folder or 
supply them via environment variables. if you do both, env vars will be used  

| text file  | environment variables | where to get |
| ------------- | ------------- | ------------- |
| token.txt  | MTD_TOKEN  | [create a new app, make a bot acc](https://discord.com/developers/applications/) |

### Installation for debugging and development
```bash
git clone https://github.com/Kyuunex/MentorshipTemplateDistributor.git -b master MTD
cd MTD
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
./run_mtd.py
```
To install a modified version of the bot for production use, type `pip3 install . --upgrade` while in the same directory

### Installation for production use
Head over to the Releases section, pick the latest release, 
and in its description you will see an installation command. 
Open the Terminal, paste that in and press enter.

To install the latest unstable version, type the following in the Terminal instead 
```bash
python3 -m pip install git+https://github.com/Kyuunex/MentorshipTemplateDistributor.git@master --upgrade
```

To run the bot, type `python3 -m mtd` in the command line

### All these amount to the following

```sh
python3 -m pip install git+https://github.com/Kyuunex/MentorshipTemplateDistributor.git@master --upgrade
mkdir -p $HOME/.local/share/MTD
# wget -O $HOME/.local/share/MTD/maindb.sqlite3 REPLACE_THIS_WITH_DIRECT_FILE_LINK # optional database backup restore
echo "your_bot_token_goes_here" | tee $HOME/.local/share/MTD/token.txt
```

### Installing the bot as a systemd service
The purpose of this is to make the bot start automatically on boot, useful for example after a power outage.  

Create the following file: `/lib/systemd/system/mtd.service`  
Inside it, put the following:
```ini
[Unit]
Description=MTD
After=network.target
StartLimitIntervalSec=0

[Service]
Restart=always
RestartSec=5
User=pi
Type=simple
ExecStart=/usr/bin/python3 -m mtd

[Install]
WantedBy=multi-user.target
```

The above assumes `pi` as a username of the user the bot will be run under. Change it if it's different. 
Make sure this is run under the same user the pip3 command was ran as.  
If you want, you can add env vars in this file in the `[Service]` section as per this example
```ini
[Service]
Environment="MTD_TOKEN=your_bot_token_goes_here"
```  

After you are done, type `sudo systemctl enable --now mtd.service` to enable and start the service.

