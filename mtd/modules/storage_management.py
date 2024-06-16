from appdirs import AppDirs
from pathlib import Path
import os

dirs = AppDirs("MTD", "Kyuunex")

if os.environ.get('MTD_DATA_DIR'):
    BOT_DATA_DIR = os.environ.get('MTD_DATA_DIR')
else:
    BOT_DATA_DIR = dirs.user_data_dir

if os.environ.get('MTD_CACHE_DIR'):
    BOT_CACHE_DIR = os.environ.get('MTD_CACHE_DIR')
else:
    BOT_CACHE_DIR = dirs.user_cache_dir

if os.environ.get('MTD_LOG_DIR'):
    BOT_LOG_DIR = os.environ.get('MTD_LOG_DIR')
else:
    BOT_LOG_DIR = dirs.user_log_dir


Path(BOT_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(BOT_CACHE_DIR).mkdir(parents=True, exist_ok=True)
Path(BOT_LOG_DIR).mkdir(parents=True, exist_ok=True)

database_file = BOT_DATA_DIR + "/maindb.sqlite3"
