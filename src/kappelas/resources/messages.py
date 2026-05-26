from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any


from kappelas._http import HttpClient, _serialize_reply_markup
from kappelas._parsers import (
    parse_delete_result,
    parse_edit_message_result,
    parse_send_carousel_result,
    parse_send_media_result,
    parse_send_result,
    parse_typing_result,
)
from kappelas.types import (
    CarouselCard,
    DeleteResult,
    EditMessageResult,
    FileInput,
    ReplyMarkup,
    SendCarouselResult,
    SendMediaResult,
    SendResult,
    TypingResult,
)



class MessagesResource:
    """Send and manage messages on behalf of a bot or user."""

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    async def send(
        self,
        chat_id:         int,
        text:            str,
        *,
        reply_markup:    ReplyMarkup | None = None,
        reply_to_id:     int | None         = None,
        delete_previous: bool               = False,
    ) -> SendResult:
        """Send a text message to *chat_id*.

        Args:
            chat_id:         Target chat ID.
            text:            Message text.
            reply_markup:    Optional keyboard markup.
            reply_to_id:     Reply to an existing message by ID.
            delete_previous: If ``True``, delete the bot's previous message first.
        """
        body: dict[str, Any] = {'chat_id': chat_id, 'text': text}
        if reply_markup    is not None:  body['reply_markup']    = _serialize_reply_markup(reply_markup)
        if reply_to_id     is not None:  body['reply_to_id']     = reply_to_id
        if delete_previous:              body['delete_previous'] = True

        raw = await self._http.post_json(f'{self._base}/sendMessage', body)
        return parse_send_result(raw)

    async def send_photo(
        self,
        chat_id:         int,
        photo:           FileInput,
        *,
        caption:         str | None          = None,
        reply_to_id:     int | None          = None,
        delete_previous: bool                = False,
        reply_markup:    ReplyMarkup | None  = None,
    ) -> SendMediaResult:
        """Send a photo (image file).

        Args:
            chat_id:         Target chat ID.
            photo:           Image bytes, file-like object, or :class:`~kappelas.types.FileData`.
            caption:         Optional caption text.
            reply_to_id:     Reply to an existing message by ID.
            delete_previous: Delete the bot's previous message first.
            reply_markup:    Optional keyboard markup.
        """
        fields = self._media_fields(chat_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendPhoto', fields, 'photo', photo
        )
        return parse_send_media_result(raw)

    async def send_video(
        self,
        chat_id:         int,
        video:           FileInput,
        *,
        caption:         str | None          = None,
        reply_to_id:     int | None          = None,
        delete_previous: bool                = False,
        reply_markup:    ReplyMarkup | None  = None,
    ) -> SendMediaResult:
        """Send a video file."""
        fields = self._media_fields(chat_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendVideo', fields, 'video', video
        )
        return parse_send_media_result(raw)

    async def send_document(
        self,
        chat_id:         int,
        document:        FileInput,
        *,
        caption:         str | None          = None,
        reply_to_id:     int | None          = None,
        delete_previous: bool                = False,
        reply_markup:    ReplyMarkup | None  = None,
    ) -> SendMediaResult:
        """Send a document / file."""
        fields = self._media_fields(chat_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendDocument', fields, 'document', document
        )
        return parse_send_media_result(raw)

    async def send_audio(
        self,
        chat_id:         int,
        audio:           FileInput,
        *,
        caption:         str | None          = None,
        reply_to_id:     int | None          = None,
        delete_previous: bool                = False,
        reply_markup:    ReplyMarkup | None  = None,
    ) -> SendMediaResult:
        """Send an audio file."""
        fields = self._media_fields(chat_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendAudio', fields, 'audio', audio
        )
        return parse_send_media_result(raw)

    async def send_carousel(
        self,
        chat_id:              int,
        carousel:             list[CarouselCard],
        *,
        text:                 str | None    = None,
        quick_reply_buttons:  list[str] | None = None,
    ) -> SendCarouselResult:
        """Send a product / card carousel.

        Args:
            chat_id:             Target chat ID.
            carousel:            List of :class:`~kappelas.types.CarouselCard` items.
            text:                Optional introductory text.
            quick_reply_buttons: Optional list of quick-reply button labels.
        """
        body: dict[str, Any] = {
            'chat_id':  chat_id,
            'carousel': [asdict(c) for c in carousel],  # type: ignore[call-overload]
        }
        if text                is not None: body['text']                = text
        if quick_reply_buttons is not None: body['quick_reply_buttons'] = quick_reply_buttons

        raw = await self._http.post_json(f'{self._base}/sendCarousel', body)
        return parse_send_carousel_result(raw)

    async def send_typing(
        self,
        chat_id:   int,
        *,
        is_typing: bool = True,
    ) -> TypingResult:
        """Show or hide the typing indicator.

        Args:
            chat_id:   Target chat ID.
            is_typing: ``True`` to show, ``False`` to hide. Defaults to ``True``.
        """
        raw = await self._http.post_json(
            f'{self._base}/sendTyping',
            {'chat_id': chat_id, 'is_typing': is_typing},
        )
        return parse_typing_result(raw)

    async def edit(
        self,
        chat_id:       int,
        message_id:    int,
        *,
        new_text:      str | None = None,
        new_extra_data: Any       = None,
    ) -> EditMessageResult:
        """Edit the text or inline keyboard of a message.

        Args:
            chat_id:        Chat that contains the message.
            message_id:     ID of the message to edit.
            new_text:       Replacement text.
            new_extra_data: Replacement inline keyboard (pass a serialisable object).
        """
        body: dict[str, Any] = {'chat_id': chat_id, 'message_id': message_id}
        if new_text       is not None: body['new_text']       = new_text
        if new_extra_data is not None: body['new_extra_data'] = new_extra_data

        raw = await self._http.post_json(f'{self._base}/editMessage', body)
        return parse_edit_message_result(raw)

    async def delete(self, chat_id: int, message_id: int) -> DeleteResult:
        """Delete a message sent by this bot/user.

        Args:
            chat_id:    Chat that contains the message.
            message_id: ID of the message to delete.
        """
        raw = await self._http.post_json(
            f'{self._base}/deleteMessage',
            {'chat_id': chat_id, 'message_id': message_id},
        )
        return parse_delete_result(raw)

    # ─── helpers ─────────────────────────────────────────────────────────────

    def _media_fields(
        self,
        chat_id:         int,
        caption:         str | None,
        reply_to_id:     int | None,
        delete_previous: bool,
        reply_markup:    ReplyMarkup | None,
    ) -> dict[str, Any]:
        """Build the non-file multipart fields for a send-media call."""
        fields: dict[str, Any] = {'chat_id': str(chat_id)}
        if caption         is not None: fields['caption']         = caption
        if reply_to_id     is not None: fields['reply_to_id']     = str(reply_to_id)
        if delete_previous:             fields['delete_previous'] = 'true'
        if reply_markup    is not None: fields['reply_markup']    = json.dumps(_serialize_reply_markup(reply_markup))
        return fields
