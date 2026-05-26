# kappelas-sdk

[![PyPI version](https://img.shields.io/pypi/v/kappelas-sdk.svg)](https://pypi.org/project/kappelas-sdk/)
[![Python version](https://img.shields.io/pypi/pyversions/kappelas-sdk.svg)](https://pypi.org/project/kappelas-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official Python SDK for the [Kappela](https://kappelas.com) messaging API.  
Build bots and personal automations — send messages, handle events, manage chats.

---

## Install

```bash
pip install kappelas-sdk
```

Requires Python 3.11+.

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
    await bot.messages.send(cb.chat_id, f'Button clicked: {cb.callback_data}')

asyncio.run(bot.start())
```

### Personal automation

```python
import asyncio
from kappelas import KappelaUser

me = KappelaUser('sk_your_api_key')

@me.on('message')
async def on_message(msg):
    print(f'New message from {msg.sender_name}: {msg.text}')

asyncio.run(me.start())
```

---

## Async usage

Every method that touches the network is a coroutine — `await` it:

```python
result = await bot.messages.send(chat_id, 'Hello!')
```

Use `asyncio.run()` as the entry point for scripts, or integrate into any async framework (FastAPI, aiohttp, etc.).

---

## Context manager

Both `KappelaBot` and `KappelaUser` support `async with`, which automatically closes the WebSocket and HTTP client on exit:

```python
async def main():
    async with KappelaBot('YOUR_BOT_TOKEN') as bot:
        await bot.messages.send(CHAT_ID, 'Hello from context manager!')
        await bot.start()

asyncio.run(main())
```

---

## Events

Register handlers with `on()` (persistent) or `once()` (fires once then auto-removes).

| Event            | Handler signature                        | Description                           |
|------------------|------------------------------------------|---------------------------------------|
| `message`        | `async def handler(msg: Message)`        | Incoming message of any type          |
| `callback_query` | `async def handler(cb: CallbackQuery)`   | Inline button clicked by a user       |
| `connected`      | `async def handler()`                    | WebSocket connected or reconnected    |
| `disconnected`   | `async def handler(code, reason)`        | WebSocket disconnected                |
| `error`          | `async def handler(exc: Exception)`      | Connection or handler error           |
| `raw`            | `async def handler(event: dict)`         | Raw `{ type, data }` wire event       |

### Decorator usage

```python
@bot.on('message')
async def on_message(msg):
    ...

@bot.once('connected')
async def on_first_connect():
    print('Connected!')
```

### Method call usage

```python
async def on_message(msg):
    ...

bot.on('message', on_message)
bot.off('message', on_message)  # remove handler
```

---

## API reference

### `KappelaBot(token, *, base_url, max_retries, timeout, ws_max_retries)`

| Parameter        | Type    | Default                        | Description                         |
|------------------|---------|--------------------------------|-------------------------------------|
| `token`          | `str`   | —                              | Bot token from BotFather            |
| `base_url`       | `str`   | `'https://api.kappelas.com'`   | API base URL                        |
| `max_retries`    | `int`   | `2`                            | HTTP retries on 429 / 5xx           |
| `timeout`        | `float` | `30.0`                         | HTTP request timeout (seconds)      |
| `ws_max_retries` | `int`   | `12`                           | WebSocket reconnect attempt limit   |

### `KappelaUser(api_key, *, base_url, max_retries, timeout, ws_max_retries)`

Same parameters as `KappelaBot` but takes a personal API key (`sk_...`).

---

## Messages

```python
# Send text
result = await bot.messages.send(chat_id, 'Hello!')

# Send with inline keyboard
from kappelas import InlineKeyboard, InlineKeyboardButton

kb = InlineKeyboard(inline_keyboard=[[
    InlineKeyboardButton(text='Click me', callback_data='btn_1'),
    InlineKeyboardButton(text='Visit', url='https://kappelas.com'),
]])
await bot.messages.send(chat_id, 'Choose:', reply_markup=kb)

# Send a photo
with open('photo.jpg', 'rb') as f:
    await bot.messages.send_photo(chat_id, f, caption='Look at this!')

# Send video
await bot.messages.send_video(chat_id, video_bytes, caption='Watch this')

# Send document
from kappelas import FileData
file = FileData(data=pdf_bytes, filename='report.pdf', content_type='application/pdf')
await bot.messages.send_document(chat_id, file)

# Send audio
await bot.messages.send_audio(chat_id, audio_bytes)

# Typing indicator
await bot.messages.send_typing(chat_id)
await bot.messages.send_typing(chat_id, is_typing=False)

# Edit a message
await bot.messages.edit(chat_id, message_id, new_text='Updated text')

# Delete a message
await bot.messages.delete(chat_id, message_id)
```

### Reply to a message

```python
await bot.messages.send(
    chat_id, 'Replying!',
    reply_to_id=original_message_id,
)
```

### Delete previous bot message

```python
await bot.messages.send(chat_id, 'New message', delete_previous=True)
```

---

## Carousel

```python
from kappelas import KappelaBot, CarouselCard

cards = [
    CarouselCard(
        id='card_1',
        title='Product A',
        subtitle='Best seller',
        image_url='https://example.com/a.jpg',
        button_text='Buy now',
    ),
    CarouselCard(id='card_2', title='Product B'),
]

result = await bot.messages.send_carousel(
    chat_id, cards,
    text='Check out our products:',
    quick_reply_buttons=['See more', 'Contact us'],
)
```

---

## Chats

```python
# Paginated list
page = await bot.chats.list(limit=20, offset=0)
print(page.chats, page.has_more)

# Iterate over all chats
async for chat in bot.chats.iterate():
    print(chat.chat_id, chat.title or chat.type)
```

---

## Webhooks

Use webhooks in production instead of a persistent WebSocket connection.

```python
# Register webhook
await bot.webhooks.set('https://your-server.com/kappela-webhook', secret='my_secret')

# Check status
info = await bot.webhooks.get_info()
print(info.active, info.url)

# Remove webhook
await bot.webhooks.delete()
```

### FastAPI integration

```python
from fastapi import FastAPI, Request
from kappelas import KappelaBot

app = FastAPI()
bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):
    await bot.messages.send(msg.chat_id, f'Echo: {msg.text}')

@app.post('/kappela-webhook')
async def webhook(request: Request):
    bot.handle_webhook(await request.json())
    return {'ok': True}
```

---

## Profile

```python
# Bot profile
profile = await bot.profile.get()
print(profile.username, profile.about)

# User profile
profile = await me.profile.get()
print(profile.nom, profile.is_premium)
```

---

## Keyboard types

### Inline keyboard (buttons inside the message)

```python
from kappelas import InlineKeyboard, InlineKeyboardButton

kb = InlineKeyboard(inline_keyboard=[
    [
        InlineKeyboardButton(text='Option A', callback_data='a'),
        InlineKeyboardButton(text='Option B', callback_data='b'),
    ],
    [
        InlineKeyboardButton(text='Open website', url='https://kappelas.com'),
    ],
])
```

### Reply keyboard (persistent input bar buttons)

```python
from kappelas import ReplyKeyboard

kb = ReplyKeyboard(keyboard=[
    ['Yes', 'No'],
    ['Cancel'],
])
```

### Scroll keyboard (horizontal scrollable chips)

```python
from kappelas import ScrollKeyboard

kb = ScrollKeyboard(scroll_keyboard=['Option 1', 'Option 2', 'Option 3'])
```

---

## File input

Media methods accept three forms of file input:

| Type               | Example                              |
|--------------------|--------------------------------------|
| `bytes`            | `open('img.jpg', 'rb').read()`       |
| `IO[bytes]`        | `open('img.jpg', 'rb')`              |
| `FileData`         | `FileData(data=b'...', filename='img.jpg', content_type='image/jpeg')` |

---

## Error handling

```python
from kappelas import KappelaError

try:
    await bot.messages.send(chat_id, 'Hello')
except KappelaError as e:
    print(e.error_code)   # 'NOT_FOUND', 'UNAUTHORIZED', etc.
    print(e.status)       # HTTP status code
    print(e.hint)         # human-readable description
    print(e.solutions)    # list of suggested fixes
    print(e.request_id)   # include when contacting support
    print(e)              # full formatted block
```

---

## License

MIT © Arnell LAWSON
