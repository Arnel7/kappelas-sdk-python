from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, IO, Literal, NamedTuple

# ─── Primitive type aliases ───────────────────────────────────────────────────

ErrorCode = Literal[
    'UNAUTHORIZED',
    'FORBIDDEN',
    'NOT_FOUND',
    'INVALID_FIELD',
    'MISSING_FIELD',
    'INTERNAL_ERROR',
    'SERVICE_UNAVAILABLE',
    'CONFLICT',
    'METHOD_NOT_ALLOWED',
    'INVALID_PATH',
    'UPSTREAM_ERROR',
]

MessageType = Literal[
    'text', 'image', 'video', 'audio', 'document',
    'system', 'poll', 'sticker', 'location', 'contact',
]

MessageStatus = Literal['sent', 'delivered', 'read']

ChatType = Literal['private', 'group', 'channel']

PrivacySetting = Literal['everyone', 'contacts', 'nobody']


# ─── File input ───────────────────────────────────────────────────────────────

class FileData(NamedTuple):
    """Named wrapper for file bytes with optional metadata."""
    data:         bytes | bytearray
    filename:     str | None = None
    content_type: str | None = None


#: Accepted file input types for media uploads.
FileInput = bytes | bytearray | IO[bytes] | FileData


# ─── Message ─────────────────────────────────────────────────────────────────

@dataclass
class ReplySnapshot:
    message_id: int
    sender_id:  str | None
    type:       MessageType
    text:       str | None
    media_id:   str | None


@dataclass
class Message:
    id:                 int
    chat_id:            int
    sender_id:          str | None
    type:               MessageType
    text:               str | None
    media_id:           str | None
    extra_data:         Any
    status:             MessageStatus
    edited_at:          int | None
    deleted_at:         int | None
    #: Unix timestamp (seconds)
    created_at:         int
    reply_to_id:        int | None
    reply_to_snapshot:  ReplySnapshot | None
    mentions:           list[str]
    forwarded_from:     Any
    expires_at:         int | None
    sender_name:        str | None = None
    sender_avatar_url:  str | None = None
    client_msg_id:      str | None = None
    width:              int | None = None
    height:             int | None = None


# ─── Chat ────────────────────────────────────────────────────────────────────

@dataclass
class Participant:
    id:         str
    #: Display name — mirrors the API field `nom`.
    nom:        str
    is_bot:     bool
    is_premium: bool
    avatar_url: str | None


@dataclass
class Chat:
    chat_id:               int
    id:                    int
    type:                  ChatType
    title:                 str | None
    participants:          list[Participant]
    #: ISO 8601 string
    last_message_at:       str | None
    #: ISO 8601 string
    created_at:            str
    created_by:            str
    is_pinned:             bool
    is_premium:            bool
    is_public:             bool
    only_admins_can_write: bool
    labels:                list[str]
    description:           str | None
    avatar_url:            str | None


# ─── Profiles ────────────────────────────────────────────────────────────────

@dataclass
class BotProfile:
    user_id:     str
    username:    str
    is_bot:      Literal[True]
    about:       str
    description: str
    avatar_url:  str | None


@dataclass
class UserProfile:
    id:              str
    username:        str
    #: Display name — mirrors the API field `nom`.
    nom:             str
    is_bot:          Literal[False]
    is_premium:      bool
    avatar_url:      str | None
    allow_group_add: PrivacySetting
    allow_calls:     PrivacySetting


# ─── Keyboards / markup ──────────────────────────────────────────────────────

@dataclass
class InlineKeyboardButton:
    text:          str
    callback_data: str | None = None
    url:           str | None = None


@dataclass
class InlineKeyboard:
    inline_keyboard: list[list[InlineKeyboardButton]]


@dataclass
class ReplyKeyboard:
    keyboard: list[list[str]]


@dataclass
class ScrollKeyboard:
    scroll_keyboard: list[str]


ReplyMarkup = InlineKeyboard | ReplyKeyboard | ScrollKeyboard


# ─── Carousel ────────────────────────────────────────────────────────────────

@dataclass
class CarouselCard:
    id:          str
    title:       str
    subtitle:    str | None = None
    image_url:   str | None = None
    button_text: str | None = None


# ─── Webhook ─────────────────────────────────────────────────────────────────

@dataclass
class WebhookInfo:
    active:     bool
    url:        str | None
    #: Unix timestamp (seconds)
    created_at: int | None


# ─── Results ─────────────────────────────────────────────────────────────────

@dataclass
class SendResult:
    message_id: int
    created_at: int


@dataclass
class SendMediaResult:
    message_id: int
    created_at: int
    media_id:   str


@dataclass
class SendCarouselResult:
    message_id: int
    created_at: int
    type:       Literal['carousel']


@dataclass
class ChatsResult:
    chats:    list[Chat]
    has_more: bool


@dataclass
class TypingResult:
    typing: bool


@dataclass
class DeleteResult:
    deleted: bool


@dataclass
class EditMessageResult:
    edited:     bool
    message_id: int


@dataclass
class WebhookSetResult:
    url:    str
    active: Literal[True]


@dataclass
class WebhookDeleteResult:
    active: Literal[False]


# ─── Callback query ──────────────────────────────────────────────────────────

@dataclass
class CallbackQuery:
    chat_id:         int
    #: UUID of the user who clicked the button.
    sender_id:       str
    #: Display name of the user who clicked. None if unresolvable.
    sender_nom:      str | None
    #: Username of the user who clicked. None if unresolvable.
    sender_username: str | None
    #: Value of `callback_data` on the button that was clicked.
    callback_data:   str
    #: Unix timestamp (seconds).
    sent_at:         int
