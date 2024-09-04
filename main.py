import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    Channel,
    Chat,
    PeerChat,
)

import logging
import os
import json
from dotenv import load_dotenv
from collections import deque

from decorators import channel_only, non_channel_only, specific_channel_only

# Load environment variables
load_dotenv()

BOT_VERSION = os.getenv("BOT_VERSION", "Unknown")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OFFICIAL_CHANNEL_ID = abs(int(os.getenv("OFFICIAL_CHANNEL_ID", 0)))

# File to store group IDs
GROUPS_FILE = "bot_groups.json"

# Store the groups where the bot is a member
bot_groups = set()

# Queue for failed messages with retry count
failed_messages = deque()

# Maximum number of retries
MAX_RETRIES = 3


def load_groups():
    global bot_groups
    try:
        if not os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, "w") as f:
                json.dump([], f)
        with open(GROUPS_FILE, "r") as f:
            bot_groups = set(abs(group_id) for group_id in json.load(f))
        logger.info(f"Loaded {len(bot_groups)} groups from {GROUPS_FILE}")
    except Exception as e:
        logger.error(f"Error loading groups: {str(e)}")
        bot_groups = set()


def save_groups():
    with open(GROUPS_FILE, "w") as f:
        json.dump(list(bot_groups), f)
    logger.info(f"Saved {len(bot_groups)} groups to {GROUPS_FILE}")


def cleanup_failed_messages(removed_group_id):
    global failed_messages
    messages_to_keep = deque()
    removed_group_id = abs(removed_group_id)
    while failed_messages:
        group, message, retries = failed_messages.popleft()
        if abs(group) != removed_group_id:
            messages_to_keep.append((group, message, retries))
    failed_messages = messages_to_keep
    logger.info(f"Cleaned up failed messages for removed group {removed_group_id}")


async def handle_chat_action(event):
    me = await event.client.get_me()
    if event.user_added and event.user_id == me.id:
        bot_groups.add(abs(event.chat_id))
        save_groups()
        logger.info(f"Bot added to group {abs(event.chat_id)}")
    elif event.user_kicked and event.user_id == me.id:
        bot_groups.discard(abs(event.chat_id))
        save_groups()
        logger.info(f"Bot removed from group {abs(event.chat_id)}")
        cleanup_failed_messages(event.chat_id)


async def send_message(client: TelegramClient, group: int, message):
    try:
        my_chat = await client.get_entity(PeerChat(group))
        if message.media:
            if isinstance(message.media, MessageMediaPhoto):
                await client.send_file(
                    my_chat, file=message.media.photo, caption=message.text
                )
            elif isinstance(message.media, MessageMediaDocument):
                await client.send_file(
                    my_chat, file=message.media.document, caption=message.text
                )
            else:
                await client.send_file(
                    my_chat, file=message.media, caption=message.text
                )
        else:
            await client.send_message(my_chat, message.text)
        logger.info(f"Message broadcasted to group {group}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to group {group}: {str(e)}")
        return False


async def broadcast_handler(event):
    logger.info(f"Received message from official channel {OFFICIAL_CHANNEL_ID}")
    if OFFICIAL_CHANNEL_ID == 0:
        logger.warning("OFFICIAL_CHANNEL_ID is not set. Skipping broadcast.")
        return

    message = event.message

    # Skip command messages
    if message.text.startswith("/"):
        logger.info(f"Ignoring command message: {message.text[:50]}...")
        return

    logger.info(
        f"Broadcasting message: {message.text[:50]}..."
    )  # Log first 50 chars of the message
    logger.info(f"Number of groups to broadcast to: {len(bot_groups)}")
    for group in bot_groups:
        logger.info(f"Attempting to send message to group {group}")
        success = await send_message(event.client, group, message)
        if not success:
            failed_messages.append((group, message, 0))  # 0 is the initial retry count


async def retry_failed_messages(client: TelegramClient):
    while True:
        await asyncio.sleep(30)  # Retry every 30 seconds
        retries = len(failed_messages)

        for _ in range(retries):
            if failed_messages:
                group, message, retry_count = failed_messages.popleft()
                if abs(group) not in bot_groups:
                    logger.info(f"Skipping retry for removed group {abs(group)}")
                    continue
                if retry_count >= MAX_RETRIES:
                    logger.warning(
                        f"Max retries reached for message to group {abs(group)}. Abandoning."
                    )
                    continue
                logger.info(
                    f"Retrying message for group {abs(group)}, attempt {retry_count + 1}"
                )
                success = await send_message(client, group, message)
                if not success:
                    failed_messages.append((group, message, retry_count + 1))


def is_channel(chat: Chat) -> bool:
    return isinstance(chat, Channel)


async def channel_id_handler(event):
    chat = await event.get_chat()
    await event.reply(f"The ID of this channel is: {abs(chat.id)}")
    logger.info(f"Reported channel ID {abs(chat.id)}")


async def start_handler(event):
    await event.reply(
        "Welcome! Use /channelid in the official channel to get its ID. Bot version: "
        + BOT_VERSION
    )
    logger.info("Start command received and processed")


async def list_groups(event):
    if bot_groups:
        groups_list = "\n".join(str(group) for group in bot_groups)
        await event.reply(f"Groups in broadcast list:\n{groups_list}")
    else:
        await event.reply("No groups in broadcast list.")
    logger.info(f"Listed groups: {bot_groups}")


async def register_group(event):
    chat: Chat = await event.get_chat()

    chat_id = abs(chat.id)
    if chat_id not in bot_groups:
        bot_groups.add(chat_id)
        save_groups()
        await event.reply(f"This group has been registered for broadcasts.")
        logger.info(f"Registered new group {chat_id}")
    else:
        await event.reply("This group is already registered for broadcasts.")
        logger.info(f"Attempted to register already registered group {chat_id}")


async def unregister_group(event):
    chat: Chat = await event.get_chat()

    chat_id = abs(chat.id)
    if chat_id in bot_groups:
        bot_groups.remove(chat_id)
        save_groups()
        await event.reply(f"This group has been unregistered from broadcasts.")
        logger.info(f"Unregistered group {chat_id}")
    else:
        await event.reply("This group is not registered for broadcasts.")
        logger.info(
            f"Attempted to unregister group not in the broadcast list {chat_id}"
        )


async def reset_all_group(event):
    bot_groups.clear()
    save_groups()
    await event.reply("All groups have been unregistered from broadcasts.")
    logger.info("Unregistered all groups from broadcast list")


# TODO: Implement import/export bot_groups.json file


async def main():
    load_groups()  # Load groups from file when starting

    client = TelegramClient("/app/sessions/broadcast_bot", API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)

    @client.on(events.ChatAction())
    async def chat_action_handler(event):
        await handle_chat_action(event)

    @client.on(events.NewMessage(chats=OFFICIAL_CHANNEL_ID))
    async def broadcast_handler_wrapper(event):
        await broadcast_handler(event)

    @client.on(events.NewMessage(pattern="/channelid"))
    @channel_only
    async def channel_id_handler_wrapper(event):
        await channel_id_handler(event)

    @client.on(events.NewMessage(pattern="/start"))
    @channel_only
    async def start_handler_wrapper(event):
        await start_handler(event)

    @client.on(events.NewMessage(pattern="/listgroups"))
    @specific_channel_only(OFFICIAL_CHANNEL_ID)
    async def list_groups_handler(event):
        await list_groups(event)

    @client.on(events.NewMessage(pattern="/resetgroup"))
    @specific_channel_only(OFFICIAL_CHANNEL_ID)
    async def reset_group_handler(event):
        await reset_all_group(event)

    @client.on(events.NewMessage(pattern="/register"))
    @non_channel_only
    async def register_handler(event):
        await register_group(event)

    @client.on(events.NewMessage(pattern="/unregister"))
    @non_channel_only
    async def unregister_handler(event):
        await unregister_group(event)

    logger.info("Bot started and waiting for events.")
    logger.info(f"Official Channel ID: {OFFICIAL_CHANNEL_ID}")

    # Start the retry mechanism
    asyncio.create_task(retry_failed_messages(client))

    # Print guidance message
    print(
        "Bot started. Use the /channelid command in your official channel to get its ID."
    )
    print("Use /listgroups to see all groups in the broadcast list.")
    print("Use /register in a group to add it to the broadcast list.")

    if OFFICIAL_CHANNEL_ID == 0:
        logger.warning(
            "OFFICIAL_CHANNEL_ID is not set. The bot will not broadcast messages until it's configured."
        )

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
