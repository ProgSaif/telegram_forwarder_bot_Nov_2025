# main.py
import os
import asyncio
import logging
from telethon import TelegramClient, events, errors
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ============================================================================
# CONFIG
# ============================================================================

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_NAME = os.environ.get("SESSION_NAME", "multi-fwd-session")

# Multiple sources and targets (comma-separated)
# Example:
# SOURCES=@ch1,@ch2,-1001234567890
# TARGETS=@t1,@t2,-1009876543210
SOURCES = [x.strip() for x in os.environ.get("SOURCES", "").split(",") if x.strip()]
TARGETS = [x.strip() for x in os.environ.get("TARGETS", "").split(",") if x.strip()]

DELAY = float(os.environ.get("DELAY", "0.5"))

# ============================================================================

if API_ID == 0 or API_HASH == "":
    raise SystemExit("ERROR: Please set API_ID and API_HASH in environment variables.")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def copy_message(target, msg):
    """Copy (not forward) message with format, media, buttons preserved."""
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


@client.on(events.NewMessage(chats=SOURCES))
async def handler(event):
    """Triggered when a new message arrives in ANY source channel."""
    msg = event.message

    if msg is None:
        return

    me = await client.get_me()

    # Avoid loops (bot sending to target → bot reading it again)
    if msg.from_id and getattr(msg.from_id, "user_id", None) == me.id:
        return

    logging.info(f"New message from source {event.chat_id}: {msg.id}")

    for target in TARGETS:
        await copy_message(target, msg)
        await asyncio.sleep(DELAY)


async def main():
    await client.start()
    me = await client.get_me()
    logging.info(f"Logged in as: {me.username or me.first_name}")
    logging.info(f"Sources: {SOURCES}")
    logging.info(f"Targets: {TARGETS}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
