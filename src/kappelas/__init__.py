"""
kappelas — Official Kappela SDK for Python.

Build bots and personal automations for the Kappela messaging platform.

Quick start::

    import asyncio
    from kappelas import KappelaBot

    bot = KappelaBot('YOUR_BOT_TOKEN')

    @bot.on('message')
    async def on_message(msg):
        await bot.reply(msg, f'Echo: {msg.text}')

    asyncio.run(bot.run())
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
    ReplyKeyboardButton,
    ScrollKeyboard,
    ScrollKeyboardButton,
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
    # Chat member management
    ChatMemberInfo,
    AddChatMemberParams,
    AddChatMemberResult,
    BanChatMemberParams,
    BanChatMemberResult,
    LeaveChatParams,
    LeaveChatResult,
    PromoteChatMemberParams,
    PromoteChatMemberResult,
    GetChatAdministratorsParams,
    GetChatAdministratorsResult,
    GetChatMemberParams,
    # Invite links
    ChatInviteLink,
    CreateChatInviteLinkParams,
    GetChatInviteLinksParams,
    GetChatInviteLinksResult,
    RevokeChatInviteLinkParams,
    RevokeChatInviteLinkResult,
    # Bot group membership
    BotGroupEntry,
    GetMyGroupsResult,
    # File input
    FileData,
    # Type aliases (Literal unions)
    MessageType,
    MessageStatus,
    ChatType,
    ParticipantRole,
    PrivacySetting,
    ErrorCode,
    ReplyMarkup,
    FileInput,
)
from .resources.communities import (
    CommunitiesResource,
    Community, CommunityMember, CommunityGroup, CommunityDetail,
    CommunityInvite, CommunityInvitePreview, CommunityJoinRequest, CommunityGroupRequest,
    CommunityActionResult, GetMyCommunitiesResult, GetCommunityInviteLinksResult,
    AcceptCommunityInviteResult,
    GetCommunityParams, CreateCommunityParams, UpdateCommunityParams,
    AddCommunityMemberParams, PromoteCommunityMemberParams, BanCommunityMemberParams,
    CreateCommunityInviteLinkParams, RevokeCommunityInviteLinkParams,
    CommunityInviteCodeParams, CommunityRequestActionParams,
    AddCommunityGroupParams, RemoveCommunityGroupParams,
)
from .resources.stories import (
    StoriesResource,
    Story, StoryView, StoryMediaUpload, StoryPreferences, StoryActionResult,
)

__version__ = '0.6.1'

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
    'ReplyKeyboardButton',
    'ScrollKeyboard',
    'ScrollKeyboardButton',
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
    # Chat member management
    'ChatMemberInfo',
    'AddChatMemberParams',
    'AddChatMemberResult',
    'BanChatMemberParams',
    'BanChatMemberResult',
    'LeaveChatParams',
    'LeaveChatResult',
    'PromoteChatMemberParams',
    'PromoteChatMemberResult',
    'GetChatAdministratorsParams',
    'GetChatAdministratorsResult',
    'GetChatMemberParams',
    # Invite links
    'ChatInviteLink',
    'CreateChatInviteLinkParams',
    'GetChatInviteLinksParams',
    'GetChatInviteLinksResult',
    'RevokeChatInviteLinkParams',
    'RevokeChatInviteLinkResult',
    # Bot group membership
    'BotGroupEntry',
    'GetMyGroupsResult',
    # Communities
    'CommunitiesResource',
    'Community', 'CommunityMember', 'CommunityGroup', 'CommunityDetail',
    'CommunityInvite', 'CommunityInvitePreview', 'CommunityJoinRequest', 'CommunityGroupRequest',
    'CommunityActionResult', 'GetMyCommunitiesResult', 'GetCommunityInviteLinksResult',
    'AcceptCommunityInviteResult',
    'GetCommunityParams', 'CreateCommunityParams', 'UpdateCommunityParams',
    'AddCommunityMemberParams', 'PromoteCommunityMemberParams', 'BanCommunityMemberParams',
    'CreateCommunityInviteLinkParams', 'RevokeCommunityInviteLinkParams',
    'CommunityInviteCodeParams', 'CommunityRequestActionParams',
    'AddCommunityGroupParams', 'RemoveCommunityGroupParams',
    # Stories
    'StoriesResource',
    'Story', 'StoryView', 'StoryMediaUpload', 'StoryPreferences', 'StoryActionResult',
    # File input
    'FileData',
    'FileInput',
    # Type aliases
    'MessageType',
    'MessageStatus',
    'ChatType',
    'ParticipantRole',
    'PrivacySetting',
    'ErrorCode',
    # Version
    '__version__',
]
