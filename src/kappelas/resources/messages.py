from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from typing import Any


from kappelas._http import HttpClient, _serialize_keyboard_button, _serialize_reply_markup
from kappelas.errors import KappelaError
from kappelas._parsers import (
    parse_delete_result,
    parse_edit_message_result,
    parse_send_carousel_result,
    parse_send_media_result,
    parse_send_result,
    parse_typing_result,
)
from kappelas.types import (
    ActionButton,
    CarouselCard,
    DeleteResult,
    EditMessageResult,
    FileInput,
    Form,
    ReplyMarkup,
    SendCarouselResult,
    SendMediaResult,
    SendResult,
    TypingResult,
)



class MessagesResource:
    """Send and manage messages on behalf of a bot or user.

    **Recipient — ``chat_id`` or ``user_id``.** Every send / edit / delete / typing
    method takes either ``chat_id`` (int) or ``user_id`` (str UUID). With ``user_id``
    the message is routed to your 1-to-1 private chat with that user: for a bot the
    conversation must already exist (``FORBIDDEN`` otherwise); for a user it is created
    on the fly (find-or-create). For ``edit`` / ``delete`` the conversation must exist.
    """

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    async def send(
        self,
        chat_id:         int | None = None,
        text:            str        = '',
        *,
        user_id:         str | None          = None,
        reply_markup:    ReplyMarkup | None  = None,
        action_button:   ActionButton | None = None,
        form:            Form | None         = None,
        reply_to_id:     int | None          = None,
        delete_previous: bool                = False,
    ) -> SendResult:
        """Send a text message.

        Args:
            chat_id:         Target chat ID (or use *user_id*).
            text:            Message text (shown as the card title / fallback for a *form*).
            user_id:         Target user UUID — routes to your private chat with them.
            reply_markup:    Optional keyboard markup.
            action_button:   Optional foot-of-bubble button (copy / link / join).
                             Takes precedence over *reply_markup*.
            form:            Optional interactive form card (choices / ranking / free text with a
                             submit button). Answers return as a ``callback_query`` whose
                             ``callback_data`` is ``"form::<json>"``. Takes precedence over the others.
            reply_to_id:     Reply to an existing message by ID.
            delete_previous: If ``True``, delete the bot's previous message first.
        """
        body: dict[str, Any] = {**self._recipient(chat_id, user_id), 'text': text}
        if reply_markup    is not None:  body['reply_markup']    = _serialize_reply_markup(reply_markup)
        if action_button   is not None:  body['action_button']   = asdict(action_button)
        if form            is not None:  body['form']            = asdict(form)
        if reply_to_id     is not None:  body['reply_to_id']     = reply_to_id
        if delete_previous:              body['delete_previous'] = True

        raw = await self._http.post_json(f'{self._base}/sendMessage', body)
        return parse_send_result(raw)

    async def close_webview(self, chat_id: int) -> dict[str, Any]:
        """Remotely close the in-app WebView opened by an ``open_webview`` action button on the
        recipient's device(s). Use it when the outcome is confirmed server-side (e.g. a payment
        webhook) instead of relying on the web page calling ``Kappelas.close()``. The event reaches
        **all** of the recipient's connected devices (personal real-time channel).

        Args:
            chat_id: Conversation whose recipient(s) should have their WebView closed.

        Returns:
            ``{"ok": True, "sent": <recipients notified>}``.
        """
        return await self._http.post_json(f'{self._base}/closeWebview', {'chat_id': chat_id})

    def _ping_typing(self, chat_id: int | None, user_id: str | None, action: str | None = None) -> None:
        """Émet un indicateur de saisie (fire-and-forget) avant l'upload d'un média,
        pour que le destinataire voie une activité durant un envoi lent (photo, vocal…).
        Un échec du ping ne doit jamais casser l'envoi réel."""
        async def _fire() -> None:
            try:
                await self.send_typing(chat_id=chat_id, user_id=user_id, is_typing=True, action=action)
            except Exception:
                pass
        try:
            asyncio.get_running_loop().create_task(_fire())
        except RuntimeError:
            pass  # pas de boucle asyncio courante (ne devrait pas arriver en contexte async)

    async def send_photo(
        self,
        chat_id:         int | None = None,
        photo:           FileInput | None = None,
        *,
        user_id:         str | None         = None,
        caption:         str | None         = None,
        reply_to_id:     int | None         = None,
        delete_previous: bool               = False,
        reply_markup:    ReplyMarkup | None = None,
    ) -> SendMediaResult:
        """Send a photo (image file).

        Args:
            chat_id:         Target chat ID (or use *user_id*).
            photo:           Image bytes, file-like object, or :class:`~kappelas.types.FileData`.
            user_id:         Target user UUID — routes to your private chat with them.
            caption:         Optional caption text.
            reply_to_id:     Reply to an existing message by ID.
            delete_previous: Delete the bot's previous message first.
            reply_markup:    Optional keyboard markup.
        """
        self._ping_typing(chat_id, user_id, 'sending_photo')
        fields = self._media_fields(chat_id, user_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendPhoto', fields, 'photo', self._require_file(photo)
        )
        return parse_send_media_result(raw)

    async def send_video(
        self,
        chat_id:         int | None = None,
        video:           FileInput | None = None,
        *,
        user_id:         str | None         = None,
        caption:         str | None         = None,
        reply_to_id:     int | None         = None,
        delete_previous: bool               = False,
        reply_markup:    ReplyMarkup | None = None,
    ) -> SendMediaResult:
        """Send a video file."""
        self._ping_typing(chat_id, user_id, 'sending_video')
        fields = self._media_fields(chat_id, user_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendVideo', fields, 'video', self._require_file(video)
        )
        return parse_send_media_result(raw)

    async def send_document(
        self,
        chat_id:         int | None = None,
        document:        FileInput | None = None,
        *,
        user_id:         str | None         = None,
        caption:         str | None         = None,
        reply_to_id:     int | None         = None,
        delete_previous: bool               = False,
        reply_markup:    ReplyMarkup | None = None,
    ) -> SendMediaResult:
        """Send a document / file."""
        self._ping_typing(chat_id, user_id, 'sending_document')
        fields = self._media_fields(chat_id, user_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendDocument', fields, 'document', self._require_file(document)
        )
        return parse_send_media_result(raw)

    async def send_audio(
        self,
        chat_id:         int | None = None,
        audio:           FileInput | None = None,
        *,
        user_id:         str | None         = None,
        caption:         str | None         = None,
        reply_to_id:     int | None         = None,
        delete_previous: bool               = False,
        reply_markup:    ReplyMarkup | None = None,
    ) -> SendMediaResult:
        """Send an audio file."""
        self._ping_typing(chat_id, user_id, 'recording_audio')
        fields = self._media_fields(chat_id, user_id, caption, reply_to_id, delete_previous, reply_markup)
        raw = await self._http.post_multipart(
            f'{self._base}/sendAudio', fields, 'audio', self._require_file(audio)
        )
        return parse_send_media_result(raw)

    async def get_file(self, media_id: str) -> dict[str, Any]:
        """Resolve a ``media_id`` to a signed download URL and its metadata.

        Returns a dict: ``{media_id, url, filename, content_type, size_bytes, expires_in}``.
        Works for any media the account/bot can access (i.e. it is a participant of the
        conversation where the media was shared) — e.g. a received voice note.
        """
        return await self._http.get(f'{self._base}/getFile?media_id={media_id}')

    async def download_file(self, media_id: str) -> bytes:
        """Resolve *and* download the raw bytes of a media file.

        Convenience over :meth:`get_file` — typically used to fetch a received voice note
        and transcribe it (speech-to-text). Downloads the short-lived signed URL directly.
        """
        import httpx
        info = await self.get_file(media_id)
        url = info.get('url') if isinstance(info, dict) else None
        if not url:
            raise KappelaError('media has no download url', 'NOT_FOUND', 404, None)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content

    async def send_carousel(
        self,
        chat_id:              int | None = None,
        carousel:             list[CarouselCard] | None = None,
        *,
        user_id:              str | None       = None,
        text:                 str | None       = None,
        quick_reply_buttons:  list[Any] | None = None,
        reply_to_id:          int | None       = None,
    ) -> SendCarouselResult:
        """Send a product / card carousel.

        Args:
            chat_id:             Target chat ID (or use *user_id*).
            carousel:            List of :class:`~kappelas.types.CarouselCard` items.
            user_id:             Target user UUID — routes to your private chat with them.
            text:                Optional introductory text.
            quick_reply_buttons: Optional list of quick-reply button labels.
                                 Accepts plain strings or
                                 :class:`~kappelas.types.ScrollKeyboardButton` objects
                                 for a separate ``callback_data``.
            reply_to_id:         Reply to an existing message by ID.
        """
        body: dict[str, Any] = {
            **self._recipient(chat_id, user_id),
            'carousel': [asdict(c) for c in (carousel or [])],  # type: ignore[call-overload]
        }
        if text                is not None: body['text']                = text
        if quick_reply_buttons is not None:
            body['quick_reply_buttons'] = [_serialize_keyboard_button(b) for b in quick_reply_buttons]
        if reply_to_id         is not None: body['reply_to_id']         = reply_to_id

        raw = await self._http.post_json(f'{self._base}/sendCarousel', body)
        return parse_send_carousel_result(raw)

    async def send_typing(
        self,
        chat_id:   int | None = None,
        *,
        user_id:   str | None = None,
        is_typing: bool       = True,
        action:    str | None = None,
    ) -> TypingResult:
        """Show or hide the typing indicator.

        Args:
            chat_id:   Target chat ID (or use *user_id*).
            user_id:   Target user UUID — routes to your private chat with them.
            is_typing: ``True`` to show, ``False`` to hide. Defaults to ``True``.
            action:    Indicateur d'activité distinct (façon Telegram) : ``recording_audio``,
                       ``sending_photo``, ``sending_video``, ``sending_document``. Envoyé
                       automatiquement par les méthodes d'envoi média. ``None`` = frappe texte.
        """
        body: dict[str, Any] = {**self._recipient(chat_id, user_id), 'is_typing': is_typing}
        if action:
            body['action'] = action
        raw = await self._http.post_json(f'{self._base}/sendTyping', body)
        return parse_typing_result(raw)

    async def edit(
        self,
        chat_id:       int | None = None,
        message_id:    int | None = None,
        *,
        user_id:       str | None = None,
        new_text:      str | None = None,
        new_extra_data: Any       = None,
    ) -> EditMessageResult:
        """Edit the text or inline keyboard of a message.

        Args:
            chat_id:        Chat that contains the message (or use *user_id*).
            message_id:     ID of the message to edit.
            user_id:        Target user UUID — the private chat must already exist.
            new_text:       Replacement text.
            new_extra_data: Replacement inline keyboard (pass a serialisable object).
        """
        if message_id is None:
            raise ValueError('message_id is required')
        body: dict[str, Any] = {**self._recipient(chat_id, user_id), 'message_id': message_id}
        if new_text       is not None: body['new_text']       = new_text
        if new_extra_data is not None: body['new_extra_data'] = new_extra_data

        raw = await self._http.post_json(f'{self._base}/editMessage', body)
        return parse_edit_message_result(raw)

    async def delete(
        self,
        chat_id:    int | None = None,
        message_id: int | None = None,
        *,
        user_id:    str | None = None,
    ) -> DeleteResult:
        """Delete a message sent by this bot/user.

        Args:
            chat_id:    Chat that contains the message (or use *user_id*).
            message_id: ID of the message to delete.
            user_id:    Target user UUID — the private chat must already exist.
        """
        if message_id is None:
            raise ValueError('message_id is required')
        raw = await self._http.post_json(
            f'{self._base}/deleteMessage',
            {**self._recipient(chat_id, user_id), 'message_id': message_id},
        )
        return parse_delete_result(raw)

    # ─── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _recipient(chat_id: int | None, user_id: str | None) -> dict[str, Any]:
        """Build the recipient part of a JSON body — chat_id or user_id."""
        if user_id is not None:
            return {'user_id': user_id}
        if chat_id is not None:
            return {'chat_id': chat_id}
        raise ValueError('either chat_id or user_id is required')

    @staticmethod
    def _require_file(file: FileInput | None) -> FileInput:
        if file is None:
            raise ValueError('a file is required')
        return file

    def _media_fields(
        self,
        chat_id:         int | None,
        user_id:         str | None,
        caption:         str | None,
        reply_to_id:     int | None,
        delete_previous: bool,
        reply_markup:    ReplyMarkup | None,
    ) -> dict[str, Any]:
        """Build the non-file multipart fields for a send-media call."""
        if user_id is not None:
            fields: dict[str, Any] = {'user_id': user_id}
        elif chat_id is not None:
            fields = {'chat_id': str(chat_id)}
        else:
            raise ValueError('either chat_id or user_id is required')
        if caption         is not None: fields['caption']         = caption
        if reply_to_id     is not None: fields['reply_to_id']     = str(reply_to_id)
        if delete_previous:             fields['delete_previous'] = 'true'
        if reply_markup    is not None: fields['reply_markup']    = json.dumps(_serialize_reply_markup(reply_markup))
        return fields
