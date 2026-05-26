from __future__ import annotations

from typing import Any

from kappelas.types import (
    BotProfile,
    CallbackQuery,
    CarouselCard,
    Chat,
    ChatsResult,
    DeleteResult,
    EditMessageResult,
    InlineKeyboard,
    InlineKeyboardButton,
    Message,
    MessageType,
    Participant,
    ReplyKeyboard,
    ReplySnapshot,
    ScrollKeyboard,
    SendCarouselResult,
    SendMediaResult,
    SendResult,
    TypingResult,
    UserProfile,
    WebhookDeleteResult,
    WebhookInfo,
    WebhookSetResult,
)

# ─── Message types set (used for flat webhook dispatch) ───────────────────────

MESSAGE_TYPES: frozenset[str] = frozenset({
    'text', 'image', 'video', 'audio', 'document',
    'system', 'poll', 'sticker', 'location', 'contact',
})


# ─── Primitive parsers ────────────────────────────────────────────────────────

def parse_reply_snapshot(d: dict[str, Any]) -> ReplySnapshot:
    return ReplySnapshot(
        message_id = int(d['message_id']),
        sender_id  = d.get('sender_id'),
        type       = d['type'],
        text       = d.get('text'),
        media_id   = d.get('media_id'),
    )


def parse_message(d: dict[str, Any]) -> Message:
    rs = d.get('reply_to_snapshot')
    return Message(
        id                = int(d['id']),
        chat_id           = int(d['chat_id']),
        sender_id         = d.get('sender_id'),
        type              = d['type'],
        text              = d.get('text'),
        media_id          = d.get('media_id'),
        extra_data        = d.get('extra_data'),
        status            = d.get('status', 'sent'),
        edited_at         = d.get('edited_at'),
        deleted_at        = d.get('deleted_at'),
        created_at        = int(d['created_at']),
        reply_to_id       = d.get('reply_to_id'),
        reply_to_snapshot = parse_reply_snapshot(rs) if rs else None,
        mentions          = list(d.get('mentions') or []),
        forwarded_from    = d.get('forwarded_from'),
        expires_at        = d.get('expires_at'),
        sender_name       = d.get('sender_name'),
        sender_avatar_url = d.get('sender_avatar_url'),
        client_msg_id     = d.get('client_msg_id'),
        width             = d.get('width'),
        height            = d.get('height'),
    )


def parse_participant(d: dict[str, Any]) -> Participant:
    return Participant(
        id         = str(d['id']),
        nom        = str(d['nom']),
        is_bot     = bool(d.get('is_bot', False)),
        is_premium = bool(d.get('is_premium', False)),
        avatar_url = d.get('avatar_url'),
    )


def parse_chat(d: dict[str, Any]) -> Chat:
    return Chat(
        chat_id               = int(d['chat_id']),
        id                    = int(d['id']),
        type                  = d['type'],
        title                 = d.get('title'),
        participants          = [parse_participant(p) for p in (d.get('participants') or [])],
        last_message_at       = d.get('last_message_at'),
        created_at            = str(d['created_at']),
        created_by            = str(d['created_by']),
        is_pinned             = bool(d.get('is_pinned', False)),
        is_premium            = bool(d.get('is_premium', False)),
        is_public             = bool(d.get('is_public', False)),
        only_admins_can_write = bool(d.get('only_admins_can_write', False)),
        labels                = list(d.get('labels') or []),
        description           = d.get('description'),
        avatar_url            = d.get('avatar_url'),
    )


def parse_bot_profile(d: dict[str, Any]) -> BotProfile:
    return BotProfile(
        user_id     = str(d['user_id']),
        username    = str(d['username']),
        is_bot      = True,
        about       = str(d.get('about', '')),
        description = str(d.get('description', '')),
        avatar_url  = d.get('avatar_url'),
    )


def parse_user_profile(d: dict[str, Any]) -> UserProfile:
    return UserProfile(
        id              = str(d['id']),
        username        = str(d['username']),
        nom             = str(d['nom']),
        is_bot          = False,
        is_premium      = bool(d.get('is_premium', False)),
        avatar_url      = d.get('avatar_url'),
        allow_group_add = d.get('allow_group_add', 'everyone'),
        allow_calls     = d.get('allow_calls', 'everyone'),
    )


def parse_webhook_info(d: dict[str, Any]) -> WebhookInfo:
    return WebhookInfo(
        active     = bool(d.get('active', False)),
        url        = d.get('url'),
        created_at = d.get('created_at'),
    )


def parse_send_result(d: dict[str, Any]) -> SendResult:
    return SendResult(
        message_id = int(d['message_id']),
        created_at = int(d['created_at']),
    )


def parse_send_media_result(d: dict[str, Any]) -> SendMediaResult:
    return SendMediaResult(
        message_id = int(d['message_id']),
        created_at = int(d['created_at']),
        media_id   = str(d['media_id']),
    )


def parse_send_carousel_result(d: dict[str, Any]) -> SendCarouselResult:
    return SendCarouselResult(
        message_id = int(d['message_id']),
        created_at = int(d['created_at']),
        type       = 'carousel',
    )


def parse_chats_result(d: dict[str, Any]) -> ChatsResult:
    return ChatsResult(
        chats    = [parse_chat(c) for c in (d.get('chats') or [])],
        has_more = bool(d.get('has_more', False)),
    )


def parse_edit_message_result(d: dict[str, Any]) -> EditMessageResult:
    return EditMessageResult(
        edited     = bool(d.get('edited', False)),
        message_id = int(d['message_id']),
    )


def parse_typing_result(d: dict[str, Any]) -> TypingResult:
    return TypingResult(typing=bool(d.get('typing', False)))


def parse_delete_result(d: dict[str, Any]) -> DeleteResult:
    return DeleteResult(deleted=bool(d.get('deleted', False)))


def parse_webhook_set_result(d: dict[str, Any]) -> WebhookSetResult:
    return WebhookSetResult(url=str(d['url']), active=True)


def parse_webhook_delete_result(d: dict[str, Any]) -> WebhookDeleteResult:
    return WebhookDeleteResult(active=False)


def parse_callback_query(d: dict[str, Any]) -> CallbackQuery:
    return CallbackQuery(
        chat_id         = int(d['chat_id']),
        sender_id       = str(d['sender_id']),
        sender_nom      = d.get('sender_nom'),
        sender_username = d.get('sender_username'),
        callback_data   = str(d['callback_data']),
        sent_at         = int(d['sent_at']),
    )


# ─── WS event parsing ─────────────────────────────────────────────────────────

def parse_ws_event(body: dict[str, Any]) -> tuple[str, Any] | None:
    """Parse a WS wire event ``{ type, data }`` into ``(event_name, typed_obj)``.

    Returns ``None`` for unknown event types.
    """
    event_type = body.get('type')
    data       = body.get('data') or {}

    if event_type == 'message':
        return ('message', parse_message(data))
    if event_type in ('callback_query', 'callback'):
        return ('callback_query', parse_callback_query(data))

    return None


# ─── Webhook event parsing (flat format) ─────────────────────────────────────

def parse_webhook_body(body: dict[str, Any]) -> tuple[str, Any] | None:
    """Parse a flat webhook payload into ``(event_name, typed_obj)``.

    The webhook format is flat (no ``data`` wrapper): ``{ type, chat_id, ... }``.
    Returns ``None`` for unknown event types.
    """
    type_ = body.get('type')
    if not isinstance(type_, str):
        return None

    if type_ == 'callback':
        cb = CallbackQuery(
            chat_id         = int(body['chat_id']),
            sender_id       = str(body['sender_id']),
            sender_nom      = body.get('sender_nom'),
            sender_username = body.get('sender_username'),
            callback_data   = str(body['callback_data']),
            sent_at         = int(body['sent_at']),
        )
        return ('callback_query', cb)

    if type_ in MESSAGE_TYPES:
        msg = Message(
            id                = int(body['message_id']),
            chat_id           = int(body['chat_id']),
            sender_id         = body.get('sender_id'),
            type              = type_,  # type: ignore[arg-type]
            text              = body.get('text'),
            media_id          = None,
            extra_data        = body.get('extra_data'),
            status            = 'sent',
            edited_at         = None,
            deleted_at        = None,
            created_at        = int(body['sent_at']),
            reply_to_id       = None,
            reply_to_snapshot = None,
            mentions          = [],
            forwarded_from    = None,
            expires_at        = None,
        )
        return ('message', msg)

    return None
