from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kappelas.types import ErrorCode

_DOCS_BASE = 'https://docs.kappelas.com/errors'

_HINTS: dict[str, dict[str, object]] = {
    'UNAUTHORIZED': {
        'description': 'Authentication failed. Your token or API key is invalid or expired.',
        'solutions': [
            'Verify your bot token is correct',
            'Ensure your API key has not been revoked',
        ],
        'slug': 'unauthorized',
    },
    'FORBIDDEN': {
        'description': 'You do not have permission to perform this action.',
        'solutions': [
            'Check that your bot is a participant in this chat',
            'Verify you have the required role (e.g. admin)',
        ],
        'slug': 'forbidden',
    },
    'NOT_FOUND': {
        'description': 'The requested resource does not exist.',
        'solutions': [
            'Check the ID is correct',
            'Make sure your bot has access to this resource',
            'List available chats with: await bot.chats.list()',
        ],
        'slug': 'not_found',
    },
    'MISSING_FIELD': {
        'description': 'A required field is missing from your request.',
        'solutions': [
            'Check the method signature — all required params must be provided',
            'See the full parameter list at the docs link below',
        ],
        'slug': 'missing_field',
    },
    'INVALID_FIELD': {
        'description': 'One or more fields contain invalid values.',
        'solutions': [
            'Verify field types match the expected types (e.g. chat_id must be a number)',
            'Check string length and format constraints',
        ],
        'slug': 'invalid_field',
    },
    'CONFLICT': {
        'description': 'The resource already exists or conflicts with an existing state.',
        'solutions': ['Check if the resource already exists before creating it'],
        'slug': 'conflict',
    },
    'INTERNAL_ERROR': {
        'description': 'An unexpected error occurred on the Kappela servers.',
        'solutions': [
            'Retry the request — this is usually transient',
            'If the problem persists, contact support with the request_id',
        ],
        'slug': 'internal_error',
    },
    'SERVICE_UNAVAILABLE': {
        'description': 'A Kappela service is temporarily unavailable.',
        'solutions': [
            'Retry with exponential backoff',
            'Check status.kappelas.com for ongoing incidents',
        ],
        'slug': 'service_unavailable',
    },
    'UPSTREAM_ERROR': {
        'description': 'An upstream Kappela service returned an unexpected response.',
        'solutions': [
            'Retry the request',
            'Check status.kappelas.com for service issues',
        ],
        'slug': 'upstream_error',
    },
    'METHOD_NOT_ALLOWED': {
        'description': 'The HTTP method used is not allowed for this endpoint.',
        'solutions': [
            'Check you are using the correct HTTP method (GET vs POST)',
            'See the API documentation for this endpoint',
        ],
        'slug': 'method_not_allowed',
    },
    'INVALID_PATH': {
        'description': 'The requested API path does not exist.',
        'solutions': [
            'Check for typos in the endpoint path',
            'Verify the SDK version matches the API version',
        ],
        'slug': 'invalid_path',
    },
}


class KappelaError(Exception):
    """Raised when the Kappela API returns an error response."""

    def __init__(
        self,
        message:    str,
        error_code: ErrorCode,
        status:     int,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code  = error_code
        self.status      = status
        self.request_id  = request_id

        hint             = _HINTS.get(error_code)
        self.hint:      str | None       = hint['description'] if hint else None  # type: ignore[index]
        self.solutions: list[str] | None = hint['solutions']   if hint else None  # type: ignore[index]

    def __str__(self) -> str:
        hint  = _HINTS.get(self.error_code)
        lines = [
            f'KappelaError: {self.args[0]}',
            f'  Code:   {self.error_code}',
            f'  Status: {self.status}',
        ]
        if hint:
            lines.append(f'\n  {hint["description"]}')
            lines.append('\n  Possible solutions:')
            for s in hint['solutions']:  # type: ignore[union-attr]
                lines.append(f'  - {s}')
            lines.append(f'\n  Docs: {_DOCS_BASE}/{hint["slug"]}')
        if self.request_id:
            lines.append(
                f'  Request ID: {self.request_id}  (mention this when contacting support)'
            )
        return '\n'.join(lines)

    def __repr__(self) -> str:
        return (
            f'KappelaError({self.args[0]!r}, error_code={self.error_code!r}, '
            f'status={self.status!r}, request_id={self.request_id!r})'
        )
