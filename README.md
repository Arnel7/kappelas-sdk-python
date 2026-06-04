# kappelas-sdk

[![PyPI version](https://img.shields.io/pypi/v/kappelas-sdk.svg)](https://pypi.org/project/kappelas-sdk/)
[![Python version](https://img.shields.io/pypi/pyversions/kappelas-sdk.svg)](https://pypi.org/project/kappelas-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-source-181717?logo=github)](https://github.com/Arnel7/kappelas-sdk-python)

**Official Python SDK for the [Kappela](https://kappelas.com) messaging platform.**  
Build bots and personal automations — send messages, handle events, manage chats.

---

## Table of contents

- [Prerequisites](#prerequisites)
- [Install](#install)
- [Quick start](#quick-start)
- [Pausing automations](#pausing-automations)
- [Python autocomplete & type hints](#python-autocomplete--type-hints)
- [Events — WebSocket vs Webhook](#events--websocket-vs-webhook)
  - [WebSocket (development)](#websocket-development)
  - [Webhook (production)](#webhook-production)
  - [Event reference](#event-reference)
  - [`bot.reply()` — convenience shorthand](#botreply--convenience-shorthand)
  - [`Message` fields](#message-fields)
  - [`CallbackQuery` fields](#callbackquery-fields)
- [API reference](#api-reference)
  - [Constructor](#constructor)
  - [messages](#messages)
  - [delete\_previous](#delete_previous)
  - [chats](#chats)
  - [Groups \& channels](#groups--channels)
  - [Receiving group messages](#receiving-group-messages)
  - [Replying to a message](#replying-to-a-message)
  - [Getting member IDs in a group](#getting-member-ids-in-a-group)
  - [Detecting conversation type](#detecting-conversation-type)
  - [Full group bot example](#full-group-bot-example)
  - [Chat member management](#chat-member-management)
  - [Invite links (admin only)](#invite-links-admin-only)
  - [getMyGroups](#getmygroups)
  - [communities](#communities)
  - [stories (KappelaUser only)](#stories-kappelauser-only)
  - [webhooks](#webhooks)
  - [profile](#profile)
- [Keyboards](#keyboards)
  - [Comparison](#comparison)
  - [Inline keyboard](#inline-keyboard--attached-to-the-message)
  - [Reply keyboard](#reply-keyboard--shown-below-the-input-bar)
  - [Scroll keyboard](#scroll-keyboard--horizontal-scrollable-chips)
  - [Full example — all three in one bot](#full-example--all-three-in-one-bot)
- [Text formatting](#text-formatting)
  - [Inline styles](#inline-styles)
  - [Block code](#block-code)
  - [Blockquote / citation](#blockquote--citation)
  - [Mentions and commands](#mentions-and-commands)
  - [Auto-detected links](#auto-detected-links)
  - [Combining formats](#combining-formats)
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
    await bot.reply(msg, f'Echo: {msg.text}')

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

**`KappelaUser` exposes the same resources as `KappelaBot`** — `me.messages`, `me.chats` (including member management and invite links), `me.communities`, `me.webhooks`, `me.profile`, and `me.reply()` — acting as yourself. In addition, `KappelaUser` has [`me.stories`](#stories-kappelauser-only) (user-only). Collections and Hugging Face credentials are bot-only.

```python
await me.reply(msg, 'Got it! 👋')
await me.communities.create(CreateCommunityParams(name='Devs', requires_approval=True))

# User-only: stories
await me.stories.create(type='text', caption='Hello 👋')
```

### Pausing automations

Pausing your personal automation makes your account stop receiving incoming messages over `/v1/me`, so an AI auto-responder is never triggered, and any send is rejected with `AUTOMATIONS_PAUSED` — until you resume. Pausing a bot makes it stop receiving incoming messages (no WebSocket push, no webhook) and rejects sends with `BOT_PAUSED` until resumed. This is useful when the human owner wants to take over and stop the AI.

```python
# Personal automation
await me.pause_automations()       # → {'automations_paused': True}
await me.resume_automations()      # → {'automations_paused': False}
await me.get_automation_status()   # → {'automations_paused': bool}

# Bot
await bot.pause()                  # → {'paused': True}
await bot.resume()                 # → {'paused': False}
await bot.get_status()             # → {'paused': bool}
```

To pause only in ONE conversation (e.g. you take over a single chat while the AI keeps handling the rest):

```python
# Personal automation, scoped to one chat
await me.pause_automation_in_chat(chat_id)    # → {'done': True}
await me.resume_automation_in_chat(chat_id)   # → {'done': True}

# Bot, scoped to one chat
await bot.pause_in_chat(chat_id)              # → {'done': True}
await bot.resume_in_chat(chat_id)             # → {'done': True}
```

---

## Python autocomplete & type hints

The SDK is fully typed — every method, parameter, and return value has a type annotation.  
Your editor (VS Code, PyCharm, etc.) will show completions and inline documentation automatically.

```python
from kappelas import KappelaBot, InlineKeyboard, InlineKeyboardButton

bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):  # msg: Message — full autocomplete on msg.chat_id, msg.text, …
    result = await bot.messages.send(  # → SendResult
        msg.chat_id,
        'Hello!',
        reply_markup=InlineKeyboard(inline_keyboard=[[
            InlineKeyboardButton(text='OK', callback_data='ok'),
        ]]),
    )
    print(result.message_id)  # int — autocomplete works here too
```

All public types are importable directly from `kappelas`:

```python
from kappelas import (
    Message, CallbackQuery, Chat, Participant,
    InlineKeyboard, InlineKeyboardButton,
    ReplyKeyboard, ReplyKeyboardButton,
    ScrollKeyboard, ScrollKeyboardButton,
    CarouselCard, FileData, KappelaError,
    ChatMemberInfo, ChatInviteLink, BotGroupEntry,
    # … and more
)
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

Both `KappelaBot` and `KappelaUser` support `async with`, which automatically closes the WebSocket and HTTP client on exit:

```python
async def main():
    async with KappelaBot('YOUR_BOT_TOKEN') as bot:
        @bot.on('message')
        async def on_message(msg):
            await bot.reply(msg, f'Echo: {msg.text}')
        await bot.run()

asyncio.run(main())
```

### Webhook (production)

```python
from fastapi import FastAPI, Request
from kappelas import KappelaBot

app = FastAPI()
bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):
    await bot.reply(msg, f'Echo: {msg.text}')

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

### Decorator vs method usage

```python
# Persistent handler — decorator form
@bot.on('message')
async def on_message(msg): ...

# Persistent handler — method form
async def on_message(msg): ...
bot.on('message', on_message)
bot.off('message', on_message)   # remove handler

# Fires once then auto-removes
@bot.once('connected')
async def on_first_connect(): ...
```

---

### `bot.reply()` — convenience shorthand

`reply()` sends a text reply without having to repeat `chat_id` and `reply_to_id` manually.

```python
bot.reply(msg, text, *, reply_markup=None, delete_previous=False)
```

- Called with a **`Message`** — sets `reply_to_id` automatically (shows a quote banner in the chat).

```python
@bot.on('message')
async def on_message(msg):
    # Simple reply
    await bot.reply(msg, 'Reçu 👍')

    # With an inline keyboard
    await bot.reply(msg, 'Choisis une option :', reply_markup=InlineKeyboard(
        inline_keyboard=[[
            InlineKeyboardButton(text='✅ Oui', callback_data='yes'),
            InlineKeyboardButton(text='❌ Non', callback_data='no'),
        ]]
    ))
```

`chat_id` and `reply_to_id` are filled automatically — you only need to set extra fields like `reply_markup` or `delete_previous`.

---

### `Message` fields

```python
@bot.on('message')
async def on_message(msg):
    msg.id                # int          — unique message ID
    msg.chat_id           # int          — conversation ID
    msg.chat_type         # str | None   — "private" | "group" | "channel"
    msg.sender_id         # str | None   — UUID of the sender (None for system messages)
    msg.type              # str          — "text" | "image" | "video" | "audio" | "document" | …
    msg.text              # str | None   — text content (None for media-only messages)
    msg.media_id          # str | None   — server-side media ID
    msg.extra_data        # Any          — inline keyboard payload (when attached)
    msg.status            # str          — "sent" | "delivered" | "read"
    msg.created_at        # int          — Unix timestamp (seconds)
    msg.edited_at         # int | None   — last edit time, or None
    msg.deleted_at        # int | None   — deletion time, or None
    msg.reply_to_id       # int | None   — ID of the message being replied to
    msg.reply_to_snapshot # ReplySnapshot | None — snapshot of the replied-to message
    msg.mentions          # list[str]    — UUIDs of mentioned users
    msg.sender_name       # str | None   — display name in groups/channels (None in private)
    msg.sender_avatar_url # str | None   — avatar URL of the sender
    msg.expires_at        # int | None   — expiry time for ephemeral messages
```

**`type` values**

| Value | Description |
|-------|-------------|
| `"text"` | Plain text message |
| `"image"` | Photo |
| `"video"` | Video |
| `"audio"` | Audio file |
| `"document"` | Generic file |
| `"sticker"` | Sticker |
| `"poll"` | Poll |
| `"location"` | Location pin |
| `"contact"` | Contact card |
| `"system"` | System notification (member joined, etc.) |

---

### `CallbackQuery` fields

```python
@bot.on('callback_query')
async def on_callback(cb):
    cb.chat_id          # int        — chat where the button was clicked
    cb.sender_id        # str        — UUID of the user who clicked
    cb.sender_name      # str | None — display name (e.g. "Arnel LAWSON")
    cb.sender_username  # str | None — username (e.g. "arnell")
    cb.callback_data    # str        — value set on the button
    cb.sent_at          # int        — Unix timestamp (seconds)
```

> Clicks are deduplicated server-side — your handler fires exactly once per click.

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
    reply_to_id   = 123,           # optional — shows a quote banner
    delete_previous = False,
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
    result = await bot.messages.send_photo(42, f, caption='Check this out!')
# → SendMediaResult(message_id=..., created_at=..., media_id=...)
```

#### `messages.send_video` / `send_document` / `send_audio` → `SendMediaResult`

Same signature — replace the file parameter with your file input.

#### `messages.send_carousel(chat_id, carousel, *, text, quick_reply_buttons, reply_to_id)` → `SendCarouselResult`

```python
from kappelas import CarouselCard, ScrollKeyboardButton

await bot.messages.send_carousel(
    chat_id  = 42,
    text     = 'Pick a product:',
    carousel = [
        CarouselCard(id='p1', title='Widget A', subtitle='9 990 FCFA', button_text='Buy'),
        CarouselCard(id='p2', title='Widget B', subtitle='19 990 FCFA', button_text='Buy'),
    ],
    quick_reply_buttons=[
        ScrollKeyboardButton(text='✅ Confirm', callback_data='confirm'),
        ScrollKeyboardButton(text='❌ Cancel',  callback_data='cancel'),
    ],
)
```

When a user clicks a carousel card button, a `callback_query` fires with `callback_data` set to the card's `id`.

#### `messages.edit(chat_id, message_id, *, new_text, new_extra_data)` → `EditMessageResult`

```python
# Edit text only
await bot.messages.edit(42, 123, new_text='Updated!')

# Edit inline keyboard only — keep existing text
from dataclasses import asdict
await bot.messages.edit(42, 123, new_extra_data=asdict(
    InlineKeyboard(inline_keyboard=[[
        InlineKeyboardButton(text='Done ✅', callback_data='done'),
    ]])
))
# → EditMessageResult(edited=True, message_id=123)
```

When `new_extra_data` is provided, `new_text` is optional — you can edit the keyboard without touching the text.

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

### `delete_previous`

Pass `delete_previous=True` on any `send*` call to automatically remove the previous message from this bot in the same chat before sending. Useful for bots that maintain a single "current state" message.

```python
# Send the first message
await bot.messages.send(chat_id, '⏳ Chargement…')

# Replace it — the previous message is deleted automatically
await bot.messages.send(chat_id, '✅ Résultat prêt !', delete_previous=True)
```

Works on all send methods: `send()`, `send_photo()`, `send_video()`, `send_document()`, `send_audio()`.

---

### `chats`

#### `chats.list(*, limit, offset)` → `ChatsResult`

```python
page = await bot.chats.list(limit=20, offset=0)
for chat in page.chats:
    print(chat.chat_id, chat.type, chat.title)
print(page.has_more)
```

#### `chats.iterate(page_size?)` → `AsyncGenerator[Chat]`

```python
async for chat in bot.chats.iterate():
    print(chat.chat_id, chat.title, chat.type)
```

**`Chat` fields**

```python
chat.chat_id              # int         — conversation ID
chat.type                 # str         — "private" | "group" | "channel"
chat.title                # str | None  — group/channel name (None for private)
chat.participants         # list[Participant] — members (private only; empty for large groups)
chat.last_message_at      # str | None  — ISO 8601 timestamp of last message
chat.created_at           # str         — ISO 8601 creation timestamp
chat.is_public            # bool        — public group or channel
chat.only_admins_can_write# bool        — only admins can post
chat.description          # str | None  — group/channel description
chat.avatar_url           # str | None  — avatar image URL
```

---

### Groups & channels

Bots work identically in private chats, groups, and channels — same API, same events. The only requirement is that **the bot must be a member** of the conversation.

#### Receiving group messages

When a bot is added to a group or channel, it automatically receives every message posted there via the same `on('message')` handler used for DMs.

```python
@bot.on('message')
async def on_message(msg):
    # msg.chat_id    — the group's id
    # msg.chat_type  — "private" | "group" | "channel"
    # msg.sender_id  — UUID of the user who sent the message
    # msg.text       — message content (None for media-only)
    pass
```

> The `chat_type` field lets you distinguish where a message came from without an extra API call.

#### Replying to a message

`reply_to_id` attaches a quote banner to your message. It works identically in private chats, groups, and channels. In groups, always quote the user you're responding to — it makes the context clear to all members.

```python
@bot.on('message')
async def on_message(msg):
    name = msg.sender_name or 'ami'
    await bot.messages.send(
        msg.chat_id,
        f'Reçu, {name} 👋',
        reply_to_id=msg.id,   # quotes the original message
    )
```

**Quoting any historical message** — `reply_to_id` accepts any message ID, not just the one that triggered the event:

```python
await bot.messages.send(
    msg.chat_id,
    'Voici la réponse à ta question précédente :',
    reply_to_id=456,  # any past message ID
)
```

**Works on all send methods** — `send_photo()`, `send_video()`, `send_document()`, `send_audio()`, and `send_carousel()` all accept `reply_to_id`:

```python
await bot.messages.send_carousel(
    msg.chat_id,
    carousel=[CarouselCard(id='p1', title='Produit A')],
    text='Voici nos produits :',
    reply_to_id=msg.id,   # banner shows above the carousel
)
```

#### Getting member IDs in a group

There are three ways to obtain the `user_id` of members in a group or channel:

**1. From incoming messages** — the simplest. `msg.sender_id` is always set on every message event:

```python
@bot.on('message')
async def on_message(msg):
    if msg.chat_type == 'group':
        print(msg.sender_id)    # UUID of the sender
        print(msg.sender_name)  # display name (None in private chats)
```

**2. From the participants list** — `chats.list()` returns the full member list for each chat:

```python
result = await bot.chats.list(limit=50)
for chat in result.chats:
    for member in chat.participants:
        print(member.id)        # UUID — use as user_id in member calls
        print(member.nom)       # display name
        print(member.is_bot)    # True if this participant is a bot
        print(member.role)      # "admin" | "member" | None (private chats)
```

**3. From `get_administrators()`** — when you only need admin IDs:

```python
from kappelas import GetChatAdministratorsParams

result = await bot.chats.get_administrators(GetChatAdministratorsParams(chat_id=42))
for admin in result.admins:
    print(admin.user_id, admin.role)  # role is always "admin"
```

#### Detecting conversation type

`msg.chat_type` is available on every incoming message. Use it to adapt bot behaviour per context:

```python
@bot.on('message')
async def on_message(msg):
    if msg.chat_type == 'private':
        # 1-on-1 chat — show full keyboard, personalise replies
        await bot.messages.send(
            msg.chat_id,
            'De quoi as-tu besoin ?',
            reply_markup=ScrollKeyboard(scroll_keyboard=[
                ScrollKeyboardButton(text='📦 Commandes', callback_data='menu_orders'),
                ScrollKeyboardButton(text='❓ Aide',      callback_data='menu_help'),
            ]),
        )

    elif msg.chat_type == 'group':
        # Multi-user — reply with a quote so context is clear
        await bot.messages.send(msg.chat_id, '✅ Noté !', reply_to_id=msg.id)

    elif msg.chat_type == 'channel':
        # Bot-only posting — no user interaction expected
        pass
```

#### Full group bot example

A bot that works across private chats, groups, and channels:

```python
import asyncio
from kappelas import KappelaBot, InlineKeyboard, InlineKeyboardButton, KappelaError
from kappelas.types import CreateChatInviteLinkParams

bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):
    if not msg.text:
        return

    # /status — works anywhere
    if msg.text == '/status':
        await bot.messages.send(
            msg.chat_id,
            '🟢 Bot en ligne',
            reply_to_id=msg.id if msg.chat_type == 'group' else None,
        )
        return

    # /invite — admin-only, group/channel only
    if msg.text == '/invite' and msg.chat_type != 'private':
        try:
            link = await bot.chats.create_invite_link(
                CreateChatInviteLinkParams(chat_id=msg.chat_id)
            )
            await bot.messages.send(
                msg.chat_id,
                f'🔗 Lien d\'invitation : {link.url}',
                reply_to_id=msg.id if msg.chat_type == 'group' else None,
            )
        except KappelaError:
            await bot.messages.send(
                msg.chat_id,
                '❌ J\'ai besoin des droits admin pour créer des liens d\'invitation.',
            )
        return

    # Private only — interactive keyboard
    if msg.chat_type == 'private':
        await bot.messages.send(
            msg.chat_id,
            'De quoi as-tu besoin ?',
            reply_markup=InlineKeyboard(inline_keyboard=[[
                InlineKeyboardButton(text='📦 Commandes', callback_data='orders'),
                InlineKeyboardButton(text='❓ Aide',      callback_data='help'),
            ]]),
        )

@bot.on('callback_query')
async def on_callback(cb):
    await bot.messages.send(cb.chat_id, f'Tu as choisi : {cb.callback_data}')

asyncio.run(bot.run())
```

---

### Chat member management

All methods below require the bot to be **a member** of the conversation.  
Methods that modify membership (`add_member`, `ban_member`, `promote_member`) additionally require **admin rights**.

#### `chats.get_administrators(params)` → `GetChatAdministratorsResult`

```python
from kappelas import GetChatAdministratorsParams

result = await bot.chats.get_administrators(GetChatAdministratorsParams(chat_id=42))
for admin in result.admins:
    print(admin.user_id, admin.role)   # role is always "admin"
```

#### `chats.get_member(params)` → `ChatMemberInfo`

Returns the role of a specific member. Raises `KappelaError(error_code='NOT_FOUND')` if the user is not in the conversation.

```python
from kappelas import GetChatMemberParams

member = await bot.chats.get_member(GetChatMemberParams(chat_id=42, user_id='user-uuid'))
print(member.role)   # "admin" | "member"
```

#### `chats.add_member(params)` → `AddChatMemberResult`

```python
from kappelas import AddChatMemberParams

await bot.chats.add_member(AddChatMemberParams(chat_id=42, user_id='user-uuid'))
```

#### `chats.ban_member(params)` → `BanChatMemberResult`

Removes (kicks) a user. To remove the bot itself, use `leave_chat()` instead.

```python
from kappelas import BanChatMemberParams

await bot.chats.ban_member(BanChatMemberParams(chat_id=42, user_id='user-uuid'))
```

#### `chats.promote_member(params)` → `PromoteChatMemberResult`

```python
from kappelas import PromoteChatMemberParams

# Promote to admin
await bot.chats.promote_member(PromoteChatMemberParams(
    chat_id=42, user_id='user-uuid', role='admin'
))

# Demote back to member
await bot.chats.promote_member(PromoteChatMemberParams(
    chat_id=42, user_id='user-uuid', role='member'
))
```

#### `chats.leave_chat(params)` → `LeaveChatResult`

```python
from kappelas import LeaveChatParams

await bot.chats.leave_chat(LeaveChatParams(chat_id=42))
```

---

### Invite links (admin only)

All invite link methods require **admin rights** in the target group or channel.

#### `chats.create_invite_link(params)` → `ChatInviteLink`

```python
from kappelas import CreateChatInviteLinkParams

# Permanent link, unlimited uses
link = await bot.chats.create_invite_link(CreateChatInviteLinkParams(chat_id=42))
print(link.url)   # "https://kappelas.com/invite/aBcD123xyz"

# Max 5 uses, expires in 24 hours
link = await bot.chats.create_invite_link(CreateChatInviteLinkParams(
    chat_id=42, max_uses=5, expires_in='24h'
))
```

`expires_in` values: `"1h"` · `"24h"` · `"7d"` · `"30d"` · `"never"` (default)

#### `chats.create_single_use_invite_link(params)` → `ChatInviteLink`

Shorthand for `create_invite_link` with `max_uses=1`.

```python
link = await bot.chats.create_single_use_invite_link(
    CreateChatInviteLinkParams(chat_id=42)
)
```

#### `chats.get_invite_links(params)` → `GetChatInviteLinksResult`

```python
from kappelas import GetChatInviteLinksParams

result = await bot.chats.get_invite_links(GetChatInviteLinksParams(chat_id=42))
for link in result.invite_links:
    max_uses = '∞' if link.max_uses == 0 else str(link.max_uses)
    print(f'{link.url} — {link.use_count}/{max_uses} uses')
```

#### `chats.revoke_invite_link(params)` → `RevokeChatInviteLinkResult`

```python
from kappelas import RevokeChatInviteLinkParams

result = await bot.chats.revoke_invite_link(RevokeChatInviteLinkParams(
    chat_id=42, code='aBcD123xyz'   # link.code from create_invite_link
))
print(result.revoked)   # True
```

---

### getMyGroups

#### `chats.get_my_groups()` → `GetMyGroupsResult`

Returns every group and channel the bot belongs to, with the bot's role in each. Useful to discover which groups the bot can manage.

```python
result = await bot.chats.get_my_groups()
for group in result.groups:
    print(group.chat_id, group.type, group.title, group.bot_role)

# Filter to groups where the bot is admin
admin_groups = [g for g in result.groups if g.bot_role == 'admin']
```

`BotGroupEntry` fields:

| Field | Type | Description |
|-------|------|-------------|
| `chat_id` | `int` | Conversation ID |
| `type` | `str` | `"group"` or `"channel"` (never `"private"`) |
| `title` | `str \| None` | Group or channel name |
| `participant_count` | `int` | Total members (including the bot) |
| `bot_role` | `str` | `"member"` or `"admin"` |

---

### `communities`

Manage **communities** with a bot (same rights as a community admin). A bot administers
a community **only if it is admin of that community**.

> ⚠️ **Distinct scopes.** Being admin of a *group* attached to a community does **not**
> make you admin of the *community*. `Community.role` is the role **in the community**.

To make someone (a person OR a bot) a community admin, it's two steps — add as member, then promote:

```python
from kappelas import (
    AddCommunityMemberParams, PromoteCommunityMemberParams, GetCommunityParams,
    CreateCommunityParams, CreateCommunityInviteLinkParams, CommunityRequestActionParams,
)

# 1) add as member   2) promote (same flow for a user or a bot)
await bot.communities.add_member(AddCommunityMemberParams(community_id=7, user_id='<uuid or bot_user_id>', role='member'))
await bot.communities.promote_member(PromoteCommunityMemberParams(community_id=7, user_id='<uuid>', role='admin'))
```

```python
# Listing
res = await bot.communities.list()
for c in res.communities:
    print(c.id, c.name, '→', c.role)        # 'member' | 'admin'
admins = await bot.communities.list_admin() # only where the bot is community admin
detail = await bot.communities.get(GetCommunityParams(community_id=7))  # community + groups + members

# CRUD
await bot.communities.create(CreateCommunityParams(name='Devs', requires_approval=True))
await bot.communities.delete(GetCommunityParams(community_id=7))   # admin
r = await bot.communities.join(GetCommunityParams(community_id=7)) # r.pending if approval-required

# Invite links (admin)
inv = await bot.communities.create_invite_link(CreateCommunityInviteLinkParams(community_id=7, max_uses=1, expires_in='24h'))
await bot.communities.get_invite_links(GetCommunityParams(community_id=7))
await bot.communities.preview_invite(CommunityInviteCodeParams(code='aBcD123'))
await bot.communities.accept_invite(CommunityInviteCodeParams(code='aBcD123'))  # bot joins via link

# Join requests (admin, when requires_approval)
reqs = await bot.communities.get_join_requests(GetCommunityParams(community_id=7))
await bot.communities.approve_join_request(CommunityRequestActionParams(community_id=7, request_id=3))

# Group requests + linking groups (admin)
await bot.communities.add_group(AddCommunityGroupParams(community_id=7, conversation_id=42))
```

Other methods: `ban_member`, `leave`, `update`, `revoke_invite_link`, `reject_join_request`,
`get_group_requests`, `approve_group_request`, `reject_group_request`, `remove_group`.

---

### `webhooks`

#### `webhooks.set(url, *, secret)` → `WebhookSetResult`

```python
await bot.webhooks.set('https://your-server.com/kappela-webhook')
```

#### `webhooks.get_info()` → `WebhookInfo`

```python
info = await bot.webhooks.get_info()
# → WebhookInfo(active=True, url='https://…', created_at=1234567890)
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
# UserProfile → id, username, nom, is_bot=False, is_premium, avatar_url, …
```

---

### `stories` (KappelaUser only)

Create and manage **stories** (ephemeral, 24 h) via `me.stories`. Available on `KappelaUser` only — their audience is based on your private-conversation contacts.

For **image/video** stories, pass `media` (bytes, a file-like object, or `FileData`) — the SDK uploads it automatically and uses the resulting media id. For **text/poll** stories, no upload is needed. You can also pass a pre-uploaded `media_id`.

```python
from kappelas import FileData

# Image story — SDK uploads the file, then creates the story
story = await me.stories.create(
    type='image',
    media=FileData(data=img_bytes, filename='photo.jpg', content_type='image/jpeg'),
    caption='Sunset 🌇',
    audience='all',  # 'all' (default) | 'selected' | 'excluded'
)

# Text story — no media
await me.stories.create(type='text', caption='Good morning ☀️')

# Restricted audience
await me.stories.create(type='text', caption='Privé', audience='selected', audience_user_ids=['<uuid>'])
```

| Method | Returns | Description |
|--------|---------|-------------|
| `stories.create(*, type, media=None, media_id=None, caption=None, audience=None, audience_user_ids=None)` | `Story` | Create a story (uploads `media` automatically for image/video). |
| `stories.upload_media(file)` | `StoryMediaUpload` | Upload story media manually and get a media id (usually unnecessary). |
| `stories.list()` | `list[Story]` | Feed of your contacts' active stories. |
| `stories.list_mine()` | `list[Story]` | Your own stories. |
| `stories.get(story_id)` | `Story` | A single story (audience-checked server-side). |
| `stories.delete(story_id)` | `StoryActionResult` | Delete one of your stories. |
| `stories.view(story_id)` | `StoryActionResult` | Mark a story as viewed. |
| `stories.get_viewers(story_id)` | `list[StoryView]` | Who viewed your story (owner only). |
| `stories.get_preferences()` | `StoryPreferences` | Your default audience preference. |
| `stories.set_preferences(audience, audience_user_ids=None)` | `StoryActionResult` | Set your default audience preference. |

> **Pause** — while automations are paused, story reads still work but creating/deleting/viewing stories is rejected with `AUTOMATIONS_PAUSED`.

---

## Keyboards

Three keyboard types can be passed as `reply_markup` on any `send*` call.

### Comparison

| | Inline | Reply | Scroll |
|---|---|---|---|
| Position | Attached to the message | Below the input bar | Horizontal chips above input |
| Stays after tap | ✅ Yes | ❌ Dismissed | ✅ Yes |
| Separate `callback_data` | ✅ Always | ✅ Yes (long form) | ✅ Yes (long form) |
| URL button | ✅ Yes | ❌ No | ❌ No |
| Layout | 2-D grid `list[list]` | 2-D grid `list[list]` | 1-D list `list` |

---

### Inline keyboard — attached to the message

Buttons stay visible after being tapped. Each button fires a `callback_query` (`callback_data`) or opens a URL (`url`).

```python
from kappelas import InlineKeyboard, InlineKeyboardButton

inline = InlineKeyboard(inline_keyboard=[
    [
        InlineKeyboardButton(text='✅ Confirmer', callback_data='yes'),
        InlineKeyboardButton(text='❌ Annuler',   callback_data='no'),
    ],
    [
        InlineKeyboardButton(text='🌐 Site web', url='https://kappelas.com'),
    ],
])
```

### Reply keyboard — shown below the input bar

Dismissed after the user taps a button. Buttons trigger a `callback_query`.

**Short form** — label and callback value are identical:

```python
from kappelas import ReplyKeyboard, ReplyKeyboardButton

reply = ReplyKeyboard(keyboard=[
    [ReplyKeyboardButton('📦 Mes commandes'), ReplyKeyboardButton('❓ Aide')],
    [ReplyKeyboardButton('🔙 Retour')],
])
```

You can also use plain strings as a shorthand when label and callback are the same:

```python
reply = ReplyKeyboard(keyboard=[
    ['📦 Mes commandes', '❓ Aide'],
    ['🔙 Retour'],
])
```

**Long form** — separate label and callback value:

```python
reply = ReplyKeyboard(keyboard=[
    [
        ReplyKeyboardButton(text='✅ Confirmer', callback_data='confirm_yes'),
        ReplyKeyboardButton(text='❌ Annuler',   callback_data='confirm_no'),
    ],
    [ReplyKeyboardButton(text='↩ Retour', callback_data='cancel')],
])
```

You can **mix** short and long buttons in the same grid:

```python
reply = ReplyKeyboard(keyboard=[[
    ReplyKeyboardButton(text='✅ Confirmer', callback_data='confirm'),
    ReplyKeyboardButton(text='❓ Aide'),   # short form — callback_data = text
]])
```

### Scroll keyboard — horizontal scrollable chips

A single row of chips, always visible above the input bar.

```python
from kappelas import ScrollKeyboard, ScrollKeyboardButton

# Short form — plain strings or ReplyKeyboardButton without callback_data
scroll = ScrollKeyboard(scroll_keyboard=[
    'Petit', 'Moyen', 'Grand', 'XL',
])

# Long form — emoji label, clean callback value
scroll = ScrollKeyboard(scroll_keyboard=[
    ScrollKeyboardButton(text='📦 Commandes', callback_data='menu_orders'),
    ScrollKeyboardButton(text='❓ Aide',      callback_data='menu_help'),
    ScrollKeyboardButton(text='⚙️ Réglages',  callback_data='menu_settings'),
])
```

```python
await bot.messages.send(
    42,
    'Choisis une option :',
    reply_markup=inline,   # or reply, or scroll
)
```

### Full example — all three in one bot

```python
import asyncio
from kappelas import (
    KappelaBot,
    InlineKeyboard, InlineKeyboardButton,
    ReplyKeyboard, ReplyKeyboardButton,
    ScrollKeyboard, ScrollKeyboardButton,
)

bot = KappelaBot('YOUR_BOT_TOKEN')

@bot.on('message')
async def on_message(msg):
    if msg.text != '/start':
        return

    # Persistent navigation chips
    await bot.messages.send(
        msg.chat_id,
        'Bienvenue ! De quoi as-tu besoin ?',
        reply_markup=ScrollKeyboard(scroll_keyboard=[
            ScrollKeyboardButton(text='📦 Commandes', callback_data='menu_orders'),
            ScrollKeyboardButton(text='❓ Aide',      callback_data='menu_help'),
        ]),
    )

@bot.on('callback_query')
async def on_callback(cb):
    if cb.callback_data == 'menu_orders':
        # Inline confirm/cancel buttons
        await bot.messages.send(
            cb.chat_id,
            'Confirmer ta dernière commande ?',
            reply_markup=InlineKeyboard(inline_keyboard=[[
                InlineKeyboardButton(text='✅ Confirmer', callback_data='order_confirm'),
                InlineKeyboardButton(text='❌ Annuler',   callback_data='order_cancel'),
            ]]),
        )

    elif cb.callback_data == 'menu_help':
        # Reply keyboard for topic selection
        await bot.messages.send(
            cb.chat_id,
            'Quel sujet ?',
            reply_markup=ReplyKeyboard(keyboard=[
                [
                    ReplyKeyboardButton(text='💳 Facturation', callback_data='help_billing'),
                    ReplyKeyboardButton(text='🚚 Livraison',   callback_data='help_delivery'),
                ],
                [ReplyKeyboardButton(text='↩ Retour au menu', callback_data='menu_back')],
            ]),
        )

asyncio.run(bot.run())
```

---

## Text formatting

Kappela renders a **WhatsApp/Telegram-style subset of Markdown** in every message bubble — bot messages, group messages, and private chat messages. All formatting is applied client-side by the Android app; you only need to send the correct markup in the `text` or `caption` field.

### Inline styles

| Syntax | Result |
|--------|--------|
| `**bold**` or `*bold*` | **Bold** |
| `__italic__` or `_italic_` | *Italic* |
| `~strikethrough~` | ~~Strikethrough~~ |
| `` `inline code` `` | Monospace with a tinted background |

```python
await bot.messages.send(
    42,
    'Commande *confirmée* ✅\nTotal : **24 990 FCFA**\nRef : `ORD-2024-001`',
)
```

### Block code

Triple backticks render as a **block code card** — only when placed on their own line.

| Position | Rendered as |
|----------|-------------|
| `` `code` `` inline | Monospace with tinted background |
| ` ```code``` ` on its own line | Full-width card + **copy** button |

```python
# Inline — stays in the text flow
await bot.messages.send(42, 'Ta ref est `ORD-2024-001` — garde-la précieusement.')

# Block — must be on its own line for the card to appear
await bot.messages.send(42, 'Ta clé API :\n```\nsk_live_abc123xyz\n```')
```

> The code card collapses to a single line with an ellipsis if the content is too long. Tapping anywhere on the card copies the content to the clipboard.

### Blockquote / citation

Prefix a line with `>` to render it as a citation banner (a `┃` bar on the left, italic, slightly faded):

```python
await bot.messages.send(
    42,
    '> Question originale ici\n\nVoici ta réponse.',
)
```

> You can combine blockquotes with `reply_to_id` — use `reply_to_id` when you want to quote a specific existing message (the app shows a reply banner); use `>` when you want to render a quote inline within the text itself.

### Mentions and commands

`@username` and `/command` are auto-detected and rendered as tappable blue links:

```python
# Mention a user by their username
await bot.messages.send(42, 'Merci @arnell, ta commande est prête !')

# Send a command hint
await bot.messages.send(42, 'Tape /help pour voir toutes les commandes disponibles.')
```

> **Protection rule:** `@` and `/` inside URLs are never formatted. `@buy_something_bot` is treated as a mention, not as `buy` + `_something_bot` (italic).

### Auto-detected links

The renderer automatically makes the following clickable without any markup:

| Pattern | Behaviour |
|---------|-----------|
| `https://…` or `http://…` | Opens in the in-app browser |
| `domain.com`, `domain.io`, `domain.fr` … | Prefixed with `https://` and opened |
| `email@example.com` | Opens the mail app |
| `+229 01 62 86 15 71`, `(229) 0162-861571` | Opens the dialler |

```python
await bot.messages.send(
    42,
    'Visitez kappelas.com ou contactez-nous à support@kappelas.com',
)
```

> **Supported domain extensions** — only the following TLDs are auto-linked:  
> `com` `org` `net` `fr` `io` `dev` `co` `me` `app` `tech` `info` `biz` `xyz` `eu` `uk` `de` `ru` `tv` `cc` `gg` `ai` `be` `ch` `ca`
>
> Country codes like `.bj`, `.sn`, `.ci` are **not** auto-detected — use a full `https://` URL instead: `https://kappelas.bj`.

> **Phone format** — any sequence of 8+ digits is detected, with spaces, dashes, and parentheses allowed: `+229 01 62 86 15 71`, `+22901628​61571`, `(229) 0162-861571` all open the dialler.

### Combining formats

All inline styles can be combined freely:

```python
lines = [
    '🛒 *Récapitulatif de commande*',
    '',
    '> Widget A × 2',
    '',
    'Total : **49 980 FCFA**',
    'Statut : `CONFIRMÉ`',
    '',
    'Des questions ? Contactez support@kappelas.com ou tapez /help',
]
await bot.messages.send(42, '\n'.join(lines))
```

Renders as:

```
🛒 Récapitulatif de commande    ← bold

┃ Widget A × 2                  ← blockquote (italic, faded)

Total : 49 980 FCFA             ← bold amount
Statut : CONFIRMÉ               ← monospace badge

Des questions ? Contactez support@kappelas.com ou tapez /help
                                ← email and /help are tappable
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
    e.solutions    # ['Check the ID is correct', …]
    e.request_id   # include when contacting support
    print(e)       # full formatted block with hints and docs link
```

### Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `UNAUTHORIZED` | 401 | Token or API key invalid / expired |
| `FORBIDDEN` | 403 | Missing permission or role (bot not in chat, not admin…) |
| `NOT_FOUND` | 404 | Resource does not exist |
| `MISSING_FIELD` | 400 | Required parameter missing |
| `INVALID_FIELD` | 400 | Parameter has wrong type or format |
| `CONFLICT` | 409 | Resource already exists |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method |
| `INVALID_PATH` | 404 | API path does not exist |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down |
| `UPSTREAM_ERROR` | 502 | Upstream service error |

> `FORBIDDEN` (not `NOT_FOUND`) is returned when the bot tries to send a message to a chat it has never joined.

---

## File input

Media methods accept files in several forms:

| Type | Example |
|------|---------|
| `bytes` | `open('img.jpg', 'rb').read()` |
| `IO[bytes]` | `open('img.jpg', 'rb')` |
| `FileData` | `FileData(data=b'…', filename='img.jpg', content_type='image/jpeg')` |

```python
from kappelas import FileData

# bytes
await bot.messages.send_photo(chat_id, open('photo.jpg', 'rb').read())

# file object
with open('photo.jpg', 'rb') as f:
    await bot.messages.send_photo(chat_id, f)

# explicit metadata — recommended for documents and audio
await bot.messages.send_document(
    chat_id,
    FileData(data=pdf_bytes, filename='report.pdf', content_type='application/pdf'),
    caption='Your monthly report',
)
```

---

## License

MIT © Arnel LAWSON
