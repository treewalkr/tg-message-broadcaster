from asyncio.log import logger
from telethon.tl.types import Channel
import functools
from typing import Optional, Callable, List
import os
import ast
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def parse_env_list(env_var_name: str, default: List[int] = []) -> List[int]:
    """Parse a list of integers from an environment variable."""
    env_value = os.getenv(env_var_name)
    if env_value is None:
        return default
    try:
        parsed_list = ast.literal_eval(env_value)
        if not isinstance(parsed_list, list):
            raise ValueError("Environment variable must be a list")
        return [int(item) for item in parsed_list]
    except (ValueError, SyntaxError) as e:
        logger.error(f"Error parsing {env_var_name}: {e}")
        return default


def chat_type_check(
    func: Callable, channel_ids: Optional[List[int]] = None, allow_channel: bool = True
):
    """Base decorator for chat type checking.

    Args:
        func (Callable): The function to be decorated.
        channel_ids (Optional[List[int]]): The list of channel IDs to allow, if any.
        allow_channel (bool): Whether to allow the command in channels or not.
    """

    @functools.wraps(func)
    async def wrapper(event):
        chat = await event.get_chat()
        is_channel_chat = isinstance(chat, Channel)

        if allow_channel:
            if channel_ids is not None:
                if is_channel_chat and chat.id in channel_ids:
                    return await func(event)
                else:
                    await event.reply("Command not allowed in this chat.")
                    logger.info(
                        f"Attempted to use channel-specific command in unauthorized chat. Chat ID: {chat.id}"
                    )
            elif is_channel_chat:
                return await func(event)
            else:
                await event.reply("Command not allowed in this chat.")
                logger.info("Attempted to use channel-only command in non-channel chat")
        else:
            if not is_channel_chat:
                return await func(event)
            else:
                await event.reply(
                    "This command can only be used in groups or private chats."
                )
                logger.info("Attempted to use non-channel command in channel chat")

    return wrapper


def channels_only(channel_ids: Optional[List[int]] = None):
    """Decorator to restrict commands to specific channels."""
    if channel_ids is None:
        channel_ids = parse_env_list("OFFICIAL_CHANNEL_IDS", [])
    return lambda func: chat_type_check(func, channel_ids=channel_ids)


def channel_only(func: Callable):
    """Decorator to restrict commands to any channel."""
    return chat_type_check(func)


def non_channel_only(func: Callable):
    """Decorator to restrict commands to non-channel chats."""
    return chat_type_check(func, allow_channel=False)


# Keep the specific_channel_only decorator for backwards compatibility
def specific_channel_only(channel_id: int):
    """Decorator to restrict commands to a specific channel."""
    return channels_only([channel_id])
