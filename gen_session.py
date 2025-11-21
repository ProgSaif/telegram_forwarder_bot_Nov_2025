from telethon.sync import TelegramClient

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

with TelegramClient('multi-fwd-session', API_ID, API_HASH) as client:
    print("Session created successfully!")
