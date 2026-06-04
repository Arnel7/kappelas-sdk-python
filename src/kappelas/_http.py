from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from kappelas.errors import KappelaError
from kappelas.types import FileData, FileInput

# ─── Constants ────────────────────────────────────────────────────────────────

_RETRY_CODES = {429, 500, 502, 503, 504}
# Backoff delays in seconds for each retry attempt
_RETRY_BACKOFF = [0.5, 1.0, 2.0]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _file_input_to_bytes_and_meta(
    file_input:       FileInput,
    default_filename: str,
) -> tuple[bytes | bytearray, str, str]:
    """Return *(data, filename, content_type)* from any FileInput."""
    if isinstance(file_input, FileData):
        data         = file_input.data
        filename     = file_input.filename or default_filename
        content_type = file_input.content_type or 'application/octet-stream'
        return data, filename, content_type

    if isinstance(file_input, (bytes, bytearray)):
        return file_input, default_filename, 'application/octet-stream'

    # IO[bytes]
    raw = file_input.read()
    name = getattr(file_input, 'name', default_filename)
    filename = name if isinstance(name, str) else default_filename
    return raw, filename, 'application/octet-stream'


def _serialize_keyboard_button(btn: Any) -> Any:
    """Serialise a ReplyKeyboardButton or plain string to its wire form.

    * ``"label"``                                → ``"label"`` (short form)
    * ``ReplyKeyboardButton(text="label")``      → ``"label"`` (short form)
    * ``ReplyKeyboardButton(text="A", callback_data="B")`` → ``{"text":"A","callback_data":"B"}``
    """
    if isinstance(btn, str):
        return btn
    cb = btn.callback_data
    if cb is None or cb == btn.text:
        return btn.text
    return {'text': btn.text, 'callback_data': cb}


def _serialize_reply_markup(rm: object) -> dict[str, Any]:
    """Convert a ReplyMarkup dataclass to a plain dict for JSON serialisation."""
    from kappelas.types import ReplyKeyboard, ScrollKeyboard
    from dataclasses import asdict

    if isinstance(rm, ReplyKeyboard):
        return {
            'keyboard': [
                [_serialize_keyboard_button(btn) for btn in row]
                for row in rm.keyboard
            ]
        }
    if isinstance(rm, ScrollKeyboard):
        return {
            'scroll_keyboard': [
                _serialize_keyboard_button(btn) for btn in rm.scroll_keyboard
            ]
        }
    # InlineKeyboard — asdict() handles nested dataclasses correctly
    return asdict(rm)  # type: ignore[arg-type]


# ─── HTTP client ──────────────────────────────────────────────────────────────

class HttpClient:
    """Async HTTP client wrapping ``httpx.AsyncClient``.

    Args:
        base_url:    Base URL, e.g. ``'https://api.kappelas.com'``.
        auth_header: Value for the ``Authorization`` header
                     (e.g. ``'Bearer <token>'`` or ``'ApiKey <key>'``).
        max_retries: How many times to retry on 429 / 5xx (default 2).
        timeout:     Per-request timeout in seconds (default 30.0).
    """

    def __init__(
        self,
        base_url:         str,
        auth_header:      str,
        max_retries:      int   = 2,
        timeout:          float = 30.0,
        auth_header_name: str   = 'Authorization',
    ) -> None:
        self._base_url    = base_url.rstrip('/')
        self._max_retries = max_retries
        self._timeout     = timeout
        self._client      = httpx.AsyncClient(
            headers={auth_header_name: auth_header},
            timeout=timeout,
        )

    # ─── Private helpers ─────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f'{self._base_url}{path}'

    async def _parse_response(self, response: httpx.Response) -> Any:
        request_id: str | None = response.headers.get('x-request-id')

        try:
            body = response.json()
        except Exception:
            raise KappelaError(
                f'Unexpected non-JSON response (HTTP {response.status_code})',
                'UPSTREAM_ERROR',
                response.status_code,
                request_id,
            )

        if not body.get('ok'):
            raise KappelaError(
                body.get('error', 'Unknown error'),
                body.get('error_code', 'INTERNAL_ERROR'),
                response.status_code,
                request_id,
            )

        return body['result']

    async def _request_with_retry(
        self,
        method:  str,
        path:    str,
        attempt: int = 0,
        **kwargs: Any,
    ) -> Any:
        response = await self._client.request(method, self._url(path), **kwargs)

        if response.status_code in _RETRY_CODES and attempt < self._max_retries:
            delay = _RETRY_BACKOFF[attempt] if attempt < len(_RETRY_BACKOFF) else 2.0
            await asyncio.sleep(delay)
            return await self._request_with_retry(method, path, attempt + 1, **kwargs)

        return await self._parse_response(response)

    # ─── Public interface ─────────────────────────────────────────────────────

    async def get(self, path: str) -> Any:
        """Send a GET request and return the ``result`` field."""
        return await self._request_with_retry('GET', path)

    async def post_json(self, path: str, body: dict[str, Any]) -> Any:
        """Send a POST request with a JSON body and return the ``result`` field."""
        return await self._request_with_retry(
            'POST', path,
            headers={'Content-Type': 'application/json'},
            content=json.dumps(body).encode(),
        )

    async def post_multipart(
        self,
        path:       str,
        fields:     dict[str, Any],
        file_field: str,
        file_input: FileInput,
    ) -> Any:
        """Send a multipart/form-data POST and return the ``result`` field."""
        data, filename, content_type = _file_input_to_bytes_and_meta(
            file_input, file_field
        )

        # httpx multipart: regular fields go in ``data``, files in ``files``
        form_data: dict[str, str] = {}
        for k, v in fields.items():
            if v is None:
                continue
            if isinstance(v, bool):
                form_data[k] = 'true' if v else 'false'
            else:
                form_data[k] = str(v)

        files = {file_field: (filename, data, content_type)}

        return await self._request_with_retry(
            'POST', path,
            data=form_data,
            files=files,
        )

    async def delete(self, path: str) -> Any:
        """Send a DELETE request and return the ``result`` field."""
        return await self._request_with_retry('DELETE', path)

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
