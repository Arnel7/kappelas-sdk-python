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

ParticipantRole = Literal['member', 'admin']


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
    #: Type of conversation ("private", "group", "channel").
    #: Always present on WS and webhook events; may be absent on history results.
    chat_type:          ChatType | None = None


# ─── Chat ────────────────────────────────────────────────────────────────────

@dataclass
class Participant:
    id:         str
    #: Display name — mirrors the API field `nom`.
    nom:        str
    is_bot:     bool
    is_premium: bool
    avatar_url: str | None
    #: Role in the conversation. Present on groups/channels; absent on private chats.
    role:       ParticipantRole | None = None


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
class ReplyKeyboardButton:
    """A button in a reply or scroll keyboard.

    Short form — label and callback value are identical::

        ReplyKeyboardButton(text="Option A")

    Long form — different label and callback value::

        ReplyKeyboardButton(text="✅ Confirm", callback_data="confirm_yes")
    """
    text:          str
    callback_data: str | None = None


#: ScrollKeyboardButton is an alias for ReplyKeyboardButton.
ScrollKeyboardButton = ReplyKeyboardButton


@dataclass
class ReplyKeyboard:
    #: Each inner list is a row; each element is a button label (str) or
    #: a :class:`ReplyKeyboardButton` for separate label / callback_data.
    keyboard: list[list[ReplyKeyboardButton | str]]


@dataclass
class ScrollKeyboard:
    #: Flat list of buttons shown as horizontal chips.
    #: Each element is a button label (str) or a :class:`ReplyKeyboardButton`.
    scroll_keyboard: list[ReplyKeyboardButton | str]


ReplyMarkup = InlineKeyboard | ReplyKeyboard | ScrollKeyboard


# ─── Action button ─────────────────────────────────────────────────────────────

#: Action button type. The meaning of ``value`` follows it:
#:
#: - ``"copy_text"``     — copies ``value`` to the clipboard (e.g. an OTP code).
#: - ``"external_link"`` — opens ``value`` (an external URL) in the system browser (leaves the app).
#: - ``"internal_link"`` — opens ``value`` as an in-app deep link.
#: - ``"join"``          — ``value`` is an invite link; tapping joins directly.
#: - ``"open_webview"``  — opens ``value`` (URL) in an in-app WebView (stays inside Kappelas). Ideal
#:   for payments: the page can close itself via ``Kappelas.close()``, or close it remotely with
#:   :meth:`MessagesResource.close_webview`.
ActionButtonType = str


@dataclass
class ActionButton:
    """A single button rendered at the foot of the message bubble (WhatsApp-style),
    distinct from inline keyboards. Performs a client-side action (copy / open / join)
    instead of firing a ``callback_query``.

    Set it via ``messages.send(..., action_button=...)``. When both ``action_button``
    and ``reply_markup`` are given, ``action_button`` takes precedence. ``label`` is
    1–100 chars, ``value`` 1–2048.
    """
    label: str
    type:  ActionButtonType  # copy_text | external_link | internal_link | join
    value: str


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
    sender_name:     str | None
    #: Username of the user who clicked. None if unresolvable.
    sender_username: str | None
    #: Value of `callback_data` on the button that was clicked.
    callback_data:   str
    #: Unix timestamp (seconds).
    sent_at:         int


# ─── Chat member management ──────────────────────────────────────────────────

@dataclass
class ChatMemberInfo:
    """Minimal member record returned by :meth:`~kappelas.resources.chats.ChatsResource.get_member`
    and :meth:`~kappelas.resources.chats.ChatsResource.get_administrators`."""
    user_id: str
    role:    ParticipantRole


@dataclass
class AddChatMemberParams:
    """Parameters for adding a user to a group or channel.

    The bot must be admin of the conversation.
    """
    chat_id: int
    user_id: str


@dataclass
class AddChatMemberResult:
    description: str


@dataclass
class BanChatMemberParams:
    """Parameters for removing (kicking) a user from a group or channel.

    The bot must be admin. To remove itself, use :class:`LeaveChatParams` instead.
    """
    chat_id: int
    user_id: str


@dataclass
class BanChatMemberResult:
    description: str


@dataclass
class LeaveChatParams:
    """Parameters for the bot to leave a group or channel."""
    chat_id: int


@dataclass
class LeaveChatResult:
    description: str


@dataclass
class PromoteChatMemberParams:
    """Parameters for changing a member's role.

    The bot must be admin.

    * ``role='admin'`` — grants admin rights
    * ``role='member'`` — revokes admin rights
    """
    chat_id: int
    user_id: str
    role:    ParticipantRole


@dataclass
class PromoteChatMemberResult:
    user_id: str
    role:    ParticipantRole


@dataclass
class GetChatAdministratorsParams:
    """Parameters for fetching all admins of a group or channel.

    The bot must be a member of the conversation.
    """
    chat_id: int


@dataclass
class GetChatAdministratorsResult:
    admins: list[ChatMemberInfo]


@dataclass
class GetChatMemberParams:
    """Parameters for looking up a single member.

    Returns :class:`ChatMemberInfo` or raises ``NOT_FOUND`` if the user is
    not in the conversation.
    """
    chat_id: int
    user_id: str


# ─── Invite links ─────────────────────────────────────────────────────────────

@dataclass
class ChatInviteLink:
    #: Short identifier used in the URL (e.g. ``"aBcD123xyz"``).
    code:       str
    #: Full invite URL (e.g. ``"https://kappelas.com/invite/aBcD123xyz"``).
    url:        str
    #: Maximum allowed uses; 0 means unlimited.
    max_uses:   int
    #: Current number of times the link has been used.
    use_count:  int
    #: Expiry as Unix timestamp (seconds), or ``None`` if permanent.
    expires_at: int | None
    #: Creation time as Unix timestamp (seconds).
    created_at: int


@dataclass
class CreateChatInviteLinkParams:
    """Parameters for creating an invite link.

    The bot must be admin of the conversation.

    Example::

        # Unlimited uses, never expires
        params = CreateChatInviteLinkParams(chat_id=42)

        # Max 5 uses, expires in 24 hours
        params = CreateChatInviteLinkParams(chat_id=42, max_uses=5, expires_in="24h")
    """
    chat_id:    int
    #: ``0`` for unlimited, or a positive number to cap uses.
    max_uses:   int = 0
    #: ``"1h"``, ``"24h"``, ``"7d"``, ``"30d"``, or ``"never"`` (default).
    expires_in: str = ''


@dataclass
class GetChatInviteLinksParams:
    """Parameters for listing all active invite links.

    The bot must be admin of the conversation.
    """
    chat_id: int


@dataclass
class GetChatInviteLinksResult:
    invite_links: list[ChatInviteLink]


@dataclass
class RevokeChatInviteLinkParams:
    """Parameters for revoking an invite link.

    The bot must be admin. ``code`` is the :attr:`ChatInviteLink.code` field.
    """
    chat_id: int
    code:    str


@dataclass
class RevokeChatInviteLinkResult:
    revoked: bool
    code:    str


# ─── Bot group membership ─────────────────────────────────────────────────────

@dataclass
class BotGroupEntry:
    """A group or channel the bot belongs to, enriched with its role."""
    #: Conversation ID — use this as ``chat_id`` in all API calls.
    chat_id:           int
    #: ``"group"`` or ``"channel"``. Never ``"private"``.
    type:              ChatType
    #: Group or channel name.
    title:             str | None
    #: Total number of members (including the bot).
    participant_count: int
    #: The bot's role in this conversation.
    bot_role:          ParticipantRole


@dataclass
class GetMyGroupsResult:
    """List of groups and channels the bot belongs to."""
    groups: list[BotGroupEntry]
