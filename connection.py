import psycopg2
import sqlite3
from read_config import read_config
import os

config_windsurf = os.path.expanduser("~/.codeium/windsurf/mcp_config.json")
config_claudde = os.path.expanduser("~/.config/Claude/claude_desktop_config.json")

def arg_value(args, key):
    if key not in args:
        return None
    idx = args.index(key)
    return args[idx + 1]

def extract_sqlite_path(url):
    # Para URLs tipo sqlite:///ruta/absoluta o sqlite:////ruta/absoluta
    if url.startswith("sqlite:///"):
        # sqlite:////home/user/file.db → /home/user/file.db
        # sqlite:///relative.db → /relative.db
        path = url.replace("sqlite:///", "/")
        return path
    elif url.startswith("sqlite://"):
        # sqlite://relative.db → relative.db
        path = url.replace("sqlite://", "")
        return path
    return url  # fallback

def connect():
    dict_config = read_config([config_windsurf, config_claudde])
    engine = arg_value(dict_config["PostgressManagement"], "--engine")
    url = arg_value(dict_config["PostgressManagement"], "--url")

    conn = ""
    if engine == "postgresql":
        conn = psycopg2.connect(url)
    elif engine == "sqlite":
        db_path = extract_sqlite_path(url)
        import os
        # Asegura que el directorio existe (si hay directorio)
        dir_name = os.path.dirname(db_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        conn = sqlite3.connect(db_path)
    else:
        conn = None
    return conn
