"""
kappelas — Official Kappela SDK for Python.

Build bots and personal automations for the Kappela messaging platform.

Quick start::

    import asyncio
    from kappelas import KappelaBot

    bot = KappelaBot('YOUR_BOT_TOKEN')

    @bot.on('message')
    async def on_message(msg):
        await bot.messages.send(msg.chat_id, f'Echo: {msg.text}')

    asyncio.run(bot.start())
"""

from kappelas.bot import KappelaBot
from kappelas.user import KappelaUser
from kappelas.errors import KappelaError
from kappelas.types import (
    # Core entities
    Message,
    CallbackQuery,
    Chat,
    Participant,
    ReplySnapshot,
    # Profiles
    BotProfile,
    UserProfile,
    # Keyboards
    InlineKeyboard,
    InlineKeyboardButton,
    ReplyKeyboard,
    ScrollKeyboard,
    # Carousel
    CarouselCard,
    # Webhook
    WebhookInfo,
    # Results
    SendResult,
    SendMediaResult,
    SendCarouselResult,
    ChatsResult,
    EditMessageResult,
    TypingResult,
    DeleteResult,
    WebhookSetResult,
    WebhookDeleteResult,
    # File input
    FileData,
    # Type aliases (Literal unions)
    MessageType,
    MessageStatus,
    ChatType,
    PrivacySetting,
    ErrorCode,
    ReplyMarkup,
    FileInput,
)

__version__ = '0.1.0'

__all__ = [
    # Main classes
    'KappelaBot',
    'KappelaUser',
    'KappelaError',
    # Core entities
    'Message',
    'CallbackQuery',
    'Chat',
    'Participant',
    'ReplySnapshot',
    # Profiles
    'BotProfile',
    'UserProfile',
    # Keyboards
    'InlineKeyboard',
    'InlineKeyboardButton',
    'ReplyKeyboard',
    'ScrollKeyboard',
    'ReplyMarkup',
    # Carousel
    'CarouselCard',
    # Webhook
    'WebhookInfo',
    # Results
    'SendResult',
    'SendMediaResult',
    'SendCarouselResult',
    'ChatsResult',
    'EditMessageResult',
    'TypingResult',
    'DeleteResult',
    'WebhookSetResult',
    'WebhookDeleteResult',
    # File input
    'FileData',
    'FileInput',
    # Type aliases
    'MessageType',
    'MessageStatus',
    'ChatType',
    'PrivacySetting',
    'ErrorCode',
    # Version
    '__version__',
]
