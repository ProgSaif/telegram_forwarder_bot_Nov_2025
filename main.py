import os
import asyncio
import logging
from telethon import TelegramClient, events, errors
from telethon.tl.types import PeerChannel, PeerChat
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ================== CONFIG ==================
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_NAME = os.environ.get("SESSION_NAME", "multi-fwd-session")

# Multiple sources and targets (comma-separated @usernames or numeric IDs)
SOURCES_RAW = [x.strip() for x in os.environ.get("SOURCES", "").split(",") if x.strip()]
TARGETS_RAW = [x.strip() for x in os.environ.get("TARGETS", "").split(",") if x.strip()]

DELAY = float(os.environ.get("DELAY", "0.5"))

# ============================================

if API_ID == 0 or API_HASH == "":
    raise SystemExit("ERROR: Please set API_ID and API_HASH in environment variables.")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def resolve_entities(raw_list):
    """Convert @username or numeric ID strings to Telethon entities"""
    entities = []
    for item in raw_list:
        try:
            ent = await client.get_entity(item)
            entities.append(ent)
        except Exception as e:
            logging.error(f"Cannot resolve entity '{item}': {e}")
    return entities

async def copy_message(target, msg):
    """Copy message with formatting, media, and buttons"""
    try:
        await client.send_message(
            entity=target,
            message=msg.message or None,
            file=msg.media or None,
            entities=getattr(msg, "entities", None),
            buttons=getattr(msg, "buttons", None),
            link_preview=True
        )
        logging.info(f"Copied msg {msg.id} → {target}")
    except errors.FloodWaitError as e:
        wait = e.seconds + 1
        logging.warning(f"FloodWait: sleeping {wait}s before retry")
        await asyncio.sleep(wait)
        await client.send_message(
            entity=target,
            message=msg.message or None,
            file=msg.media or None,
            entities=getattr(msg, "entities", None),
            buttons=getattr(msg, "buttons", None),
            link_preview=True
        )
    except Exception as ex:
        logging.error(f"Error copying msg → {target}: {ex}")

@client.on(events.NewMessage())
async def handler(event):
    msg = event.message
    if msg is None:
        return

    me = await client.get_me()
    if msg.from_id and getattr(msg.from_id, "user_id", None) == me.id:
        return

    # Only process messages from resolved sources  
    if event.chat_id not in [s.id for s in client.sources_entities]:
        return

    logging.info(f"New message from source {event.chat_id}: {msg.id}")

    for target in client.targets_entities:
        await copy_message(target, msg)
        await asyncio.sleep(DELAY)

async def main():
    await client.start()
    me = await client.get_me()
    logging.info(f"Logged in as: {me.username or me.first_name}")

    # Resolve all source and target entities
    client.sources_entities = await resolve_entities(SOURCES_RAW)
    client.targets_entities = await resolve_entities(TARGETS_RAW)

    logging.info(f"Sources resolved: {[e.id for e in client.sources_entities]}")
    logging.info(f"Targets resolved: {[e.id for e in client.targets_entities]}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
