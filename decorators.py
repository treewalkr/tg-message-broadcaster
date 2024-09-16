from asyncio.log import logger
from telethon.tl.types import Channel
import functools
from typing import Optional, Callable


def chat_type_check(
    func: Callable, channel_id: Optional[int] = None, allow_channel: bool = True
):
    """Base decorator for chat type checking.

    Args:
        func (Callable): The function to be decorated.
        channel_id (Optional[int]): The ID of the specific channel to allow, if any.
        allow_channel (bool): Whether to allow the command in channels or not.
    """

    @functools.wraps(func)
    async def wrapper(event):
        chat = await event.get_chat()
        is_channel_chat = isinstance(chat, Channel)

        if allow_channel:
            if channel_id is not None:
                if is_channel_chat and chat.id == channel_id:
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


def specific_channel_only(channel_id: int):
    """Decorator to restrict commands to a specific channel."""
    return lambda func: chat_type_check(func, channel_id=channel_id)


def channel_only(func: Callable):
    """Decorator to restrict commands to any channel."""
    return chat_type_check(func)


def non_channel_only(func: Callable):
    """Decorator to restrict commands to non-channel chats."""
    return chat_type_check(func, allow_channel=False)
