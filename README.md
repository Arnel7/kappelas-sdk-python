# kappelas-sdk

[![PyPI version](https://img.shields.io/pypi/v/kappelas-sdk.svg)](https://pypi.org/project/kappelas-sdk/)
[![Python version](https://img.shields.io/pypi/pyversions/kappelas-sdk.svg)](https://pypi.org/project/kappelas-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Official Python SDK for the [Kappela](https://kappelas.com) messaging platform.**  
Build bots and personal automations — send messages, handle events, manage chats.

---

## Table of contents

- [Prerequisites](#prerequisites)
- [Install](#install)
- [Quick start](#quick-start)
- [Async-first design](#async-first-design)
- [Events — WebSocket vs Webhook](#events--websocket-vs-webhook)
- [API reference](#api-reference)
  - [messages](#messages)
  - [chats](#chats)
  - [webhooks](#webhooks)
  - [profile](#profile)
- [Keyboards](#keyboards)
- [Error handling](#error-handling)
- [File input](#file-input)

---

## Prerequisites

You need a bot token from **BotMother**, the official Kappela bot manager.

1. Open Kappela and start a conversation with [**BotMother**](https://kappelas.com/bot/botmother_bot)
2. Follow the instructions to create a bot
3. BotMother gives you a token — keep it secret, it gives full control over your bot

For personal automation (sending messages as yourself), generate an API key from your Kappela account settings (`sk_...`).

---

## Install

```bash
pip install kappelas-sdk
```

Requires **Python 3.11+**.

---

## Quick start

### Bot

```python
import asyncio
from kappelas import KappelaBot

bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):
    await bot.messages.send(msg.chat_id, f'Echo: {msg.text}')

@bot.on('callback_query')
async def on_callback(cb):
    await bot.messages.send(cb.chat_id, f'You clicked: {cb.callback_data}')

asyncio.run(bot.run())
```

### Personal automation

```python
import asyncio
from kappelas import KappelaUser

me = KappelaUser('sk_your_api_key')

@me.on('message')
async def on_message(msg):
    print(f'[{msg.chat_id}] {msg.sender_name}: {msg.text}')

asyncio.run(me.run())
```

---

## Async-first design

Every method that touches the network is a coroutine — `await` it:

```python
result = await bot.messages.send(chat_id, 'Hello!')
```

Use `asyncio.run()` as the entry point for standalone scripts, or integrate into any async framework (FastAPI, aiohttp, etc.).

Both `KappelaBot` and `KappelaUser` support `async with`, which automatically closes the WebSocket and HTTP client on exit:

```python
async def main():
    async with KappelaBot('YOUR_BOT_TOKEN') as bot:
        @bot.on('message')
        async def on_message(msg):
            await bot.messages.send(msg.chat_id, f'Echo: {msg.text}')

        await bot.run()

asyncio.run(main())
```

---

## Events — WebSocket vs Webhook

| Mode | Method | Best for |
|------|--------|----------|
| **WebSocket** | `await bot.run()` | Development, local scripts |
| **Webhook** | `await bot.webhooks.set()` + `bot.handle_webhook()` | Production servers |

The same `on('message')` and `on('callback_query')` handlers work in both modes — no code change needed when switching.

### WebSocket (development)

```python
bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg): ...

@bot.on('callback_query')
async def on_callback(cb): ...

asyncio.run(bot.run())   # blocks, auto-reconnects on disconnect
```

`run()` blocks until `stop()` is called. Use `start()` if you need to connect in the background inside an already-running event loop.

### Webhook (production)

```python
from fastapi import FastAPI, Request
from kappelas import KappelaBot

app = FastAPI()
bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):
    await bot.messages.send(msg.chat_id, f'Echo: {msg.text}')

@bot.on('callback_query')
async def on_callback(cb):
    await bot.messages.send(cb.chat_id, f'Clicked: {cb.callback_data}')

@app.on_event('startup')
async def register_webhook():
    await bot.webhooks.set('https://your-server.com/kappela-webhook')

@app.post('/kappela-webhook')
async def webhook(request: Request):
    bot.handle_webhook(await request.json())
    return {'ok': True}
```

> Do **not** call `bot.run()` in webhook mode.

### Event reference

| Event | Handler signature | Description |
|-------|-------------------|-------------|
| `message` | `async def handler(msg: Message)` | Incoming message of any type |
| `callback_query` | `async def handler(cb: CallbackQuery)` | Inline button clicked by a user |
| `connected` | `async def handler()` | WebSocket connected or reconnected |
| `disconnected` | `async def handler(code, reason)` | WebSocket disconnected |
| `error` | `async def handler(exc: Exception)` | Connection or handler error |
| `raw` | `async def handler(event: dict)` | Raw `{ type, data }` wire event |

### `CallbackQuery` fields

```python
@bot.on('callback_query')
async def on_callback(cb):
    cb.chat_id          # int         — chat where the button was clicked
    cb.sender_id        # str         — UUID of the user who clicked
    cb.sender_nom       # str | None  — display name (e.g. "Arnel LAWSON")
    cb.sender_username  # str | None  — username (e.g. "arnell")
    cb.callback_data    # str         — value set on the button
    cb.sent_at          # int         — Unix timestamp (seconds)
```

> Clicks are deduplicated server-side — your handler fires exactly once per click.

### Decorator vs method usage

```python
# Decorator (persistent)
@bot.on('message')
async def on_message(msg): ...

# Method call (persistent)
async def on_message(msg): ...
bot.on('message', on_message)
bot.off('message', on_message)   # remove handler

# fires once then auto-removes
@bot.once('connected')
async def on_first_connect(): ...
```

---

## API reference

### Constructor

#### `KappelaBot(token, *, base_url, max_retries, timeout, ws_max_retries)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token` | `str` | — | Bot token from BotMother (required) |
| `base_url` | `str` | `'https://api.kappelas.com'` | Override API base URL |
| `max_retries` | `int` | `2` | HTTP retry count on 429 / 5xx |
| `timeout` | `float` | `30.0` | Per-request timeout (seconds) |
| `ws_max_retries` | `int` | `12` | Max WebSocket reconnect attempts |

#### `KappelaUser(api_key, *, base_url, max_retries, timeout, ws_max_retries)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | — | Personal API key `sk_...` (required) |
| `base_url` | `str` | `'https://api.kappelas.com'` | Override API base URL |
| `max_retries` | `int` | `2` | HTTP retry count on 429 / 5xx |
| `timeout` | `float` | `30.0` | Per-request timeout (seconds) |
| `ws_max_retries` | `int` | `12` | Max WebSocket reconnect attempts |

---

### `messages`

#### `messages.send(chat_id, text, *, reply_markup, reply_to_id, delete_previous)` → `SendResult`

```python
result = await bot.messages.send(
    chat_id       = 42,
    text          = 'Hello!',
    reply_to_id   = 123,           # optional — reply to a message
    delete_previous = False,       # optional
    reply_markup  = InlineKeyboard(inline_keyboard=[[
        InlineKeyboardButton(text='Yes', callback_data='yes'),
        InlineKeyboardButton(text='No',  callback_data='no'),
    ]]),
)
# → SendResult(message_id=..., created_at=...)
```

#### `messages.send_photo(chat_id, photo, *, caption, reply_to_id, delete_previous, reply_markup)` → `SendMediaResult`

```python
with open('banner.png', 'rb') as f:
    await bot.messages.send_photo(chat_id, f, caption='Check this out!')
# → SendMediaResult(message_id=..., created_at=..., media_id=...)
```

#### `messages.send_video` / `send_document` / `send_audio` → `SendMediaResult`

Same signature — replace the file parameter (`video`, `document`, `audio`) with your file.

#### `messages.send_carousel(chat_id, carousel, *, text, quick_reply_buttons)` → `SendCarouselResult`

```python
from kappelas import CarouselCard

await bot.messages.send_carousel(
    chat_id  = 42,
    text     = 'Pick a product:',
    carousel = [
        CarouselCard(id='p1', title='Widget A', subtitle='$9.99',  button_text='Buy'),
        CarouselCard(id='p2', title='Widget B', subtitle='$19.99', button_text='Buy'),
    ],
    quick_reply_buttons=['See more', 'Cancel'],
)
```

#### `messages.edit(chat_id, message_id, *, new_text, new_extra_data)` → `EditMessageResult`

```python
# Edit text
await bot.messages.edit(42, 123, new_text='Updated!')

# Edit inline keyboard only (no text change)
await bot.messages.edit(42, 123, new_extra_data={
    'inline_keyboard': [[{'text': 'Done ✅', 'callback_data': 'done'}]]
})
# → EditMessageResult(edited=True, message_id=...)
```

#### `messages.send_typing(chat_id, *, is_typing)` → `TypingResult`

```python
await bot.messages.send_typing(42)                      # show
await bot.messages.send_typing(42, is_typing=False)     # hide
```

#### `messages.delete(chat_id, message_id)` → `DeleteResult`

```python
await bot.messages.delete(42, 123)
# → DeleteResult(deleted=True)
```

---

### `chats`

#### `chats.list(*, limit, offset)` → `ChatsResult`

```python
page = await bot.chats.list(limit=20, offset=0)
print(page.chats, page.has_more)
```

#### `chats.iterate(page_size?)` → `AsyncGenerator[Chat]`

```python
async for chat in bot.chats.iterate():
    print(chat.chat_id, chat.title, chat.type)
```

---

### `webhooks`

#### `webhooks.set(url, *, secret)` → `WebhookSetResult`

```python
await bot.webhooks.set('https://your-server.com/kappela-webhook')
```

#### `webhooks.get_info()` → `WebhookInfo`

```python
info = await bot.webhooks.get_info()
# → WebhookInfo(active=True, url='https://...', created_at=...)
```

#### `webhooks.delete()` → `WebhookDeleteResult`

```python
await bot.webhooks.delete()
# → WebhookDeleteResult(active=False)
```

---

### `profile`

#### `profile.get()` → `BotProfile | UserProfile`

```python
profile = await bot.profile.get()
# BotProfile  → user_id, username, is_bot=True, about, description, avatar_url
# UserProfile → id, username, nom, is_bot=False, is_premium, avatar_url, ...
```

---

## Keyboards

Three types of keyboard can be passed as `reply_markup` on any `send*` call:

```python
from kappelas import InlineKeyboard, InlineKeyboardButton, ReplyKeyboard, ScrollKeyboard

# Inline buttons — attached to the message
inline = InlineKeyboard(inline_keyboard=[
    [
        InlineKeyboardButton(text='Yes', callback_data='yes'),
        InlineKeyboardButton(text='No',  callback_data='no'),
    ],
    [
        InlineKeyboardButton(text='Open website', url='https://kappelas.com'),
    ],
])

# Reply keyboard — shown below the input bar
reply = ReplyKeyboard(keyboard=[
    ['Option A', 'Option B'],
    ['Cancel'],
])

# Scroll keyboard — horizontal scrollable chips
scroll = ScrollKeyboard(scroll_keyboard=['Small', 'Medium', 'Large'])
```

---

## Error handling

All API errors raise `KappelaError` with structured fields:

```python
from kappelas import KappelaError

try:
    await bot.messages.send(999, 'Hi')
except KappelaError as e:
    e.error_code   # 'NOT_FOUND'
    e.status       # 404
    e.hint         # 'The requested resource does not exist.'
    e.solutions    # ['Check the ID is correct', ...]
    e.request_id   # include when contacting support
    print(e)       # full formatted block
```

### Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `UNAUTHORIZED` | 401 | Token or API key invalid / expired |
| `FORBIDDEN` | 403 | Missing permission or role |
| `NOT_FOUND` | 404 | Resource does not exist |
| `MISSING_FIELD` | 400 | Required parameter missing |
| `INVALID_FIELD` | 400 | Parameter has wrong type or format |
| `CONFLICT` | 409 | Resource already exists |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method |
| `INVALID_PATH` | 404 | API path does not exist |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down |
| `UPSTREAM_ERROR` | 502 | Upstream service error |

---

## File input

Media methods accept files in several forms:

| Type | Example |
|------|---------|
| `bytes` | `open('img.jpg', 'rb').read()` |
| `IO[bytes]` | `open('img.jpg', 'rb')` |
| `FileData` | `FileData(data=b'...', filename='img.jpg', content_type='image/jpeg')` |

```python
from kappelas import FileData

# bytes
await bot.messages.send_photo(chat_id, open('photo.jpg', 'rb').read())

# file object
with open('photo.jpg', 'rb') as f:
    await bot.messages.send_photo(chat_id, f)

# explicit metadata
await bot.messages.send_document(
    chat_id,
    FileData(data=pdf_bytes, filename='report.pdf', content_type='application/pdf'),
)
```

---

## License

MIT © Arnel LAWSON
