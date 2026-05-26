from __future__ import annotations

from kappelas._http import HttpClient
from kappelas._parsers import (
    parse_webhook_delete_result,
    parse_webhook_info,
    parse_webhook_set_result,
)
from kappelas.types import WebhookDeleteResult, WebhookInfo, WebhookSetResult


class WebhooksResource:
    """Manage Kappela webhooks."""

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    async def set(
        self,
        url: str,
        *,
        secret: str | None = None,
    ) -> WebhookSetResult:
        """Register a webhook URL.

        Args:
            url:    Public HTTPS URL where Kappela will POST events.
            secret: Optional shared secret for request verification.
        """
        body: dict[str, object] = {'url': url}
        if secret is not None:
            body['secret'] = secret

        raw = await self._http.post_json(f'{self._base}/setWebhook', body)
        return parse_webhook_set_result(raw)

    async def get_info(self) -> WebhookInfo:
        """Return current webhook status and URL."""
        raw = await self._http.get(f'{self._base}/getWebhookInfo')
        return parse_webhook_info(raw)

    async def delete(self) -> WebhookDeleteResult:
        """Remove the webhook. Events will no longer be delivered via HTTP POST."""
        raw = await self._http.post_json(f'{self._base}/deleteWebhook', {})
        return parse_webhook_delete_result(raw)
