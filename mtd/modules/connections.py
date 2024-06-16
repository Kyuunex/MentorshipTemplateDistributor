import os
from mtd.modules.storage_management import BOT_DATA_DIR

if os.environ.get('MTD_TOKEN'):
    bot_token = os.environ.get('MTD_TOKEN')
else:
    try:
        with open(BOT_DATA_DIR + "/token.txt", "r+") as token_file:
            bot_token = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a bot token. either set MTD_TOKEN environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit
