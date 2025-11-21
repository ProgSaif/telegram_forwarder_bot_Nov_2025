import os
from telethon.sync import TelegramClient

def generate_session(api_id, api_hash, session_name):
    if os.path.exists(f"{session_name}.session"):
        print(f"Session {session_name}.session already exists.")
        return

    with TelegramClient(session_name, api_id, api_hash) as client:
        print(f"Session {session_name}.session created successfully!")
