"""Stories (éphémères 24 h) pour les comptes utilisateur (``me.stories``).

Fonctionnalité réservée aux utilisateurs (l'audience est basée sur les contacts
en conversation privée) — non disponible pour les bots. Pour une story image/vidéo,
le SDK uploade le fichier automatiquement (comme ``messages.send_photo``) puis crée
la story.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .._http import HttpClient
from ..types import FileInput

# ─── Types ──────────────────────────────────────────────────────────────────


@dataclass
class Story:
    id: str
    user_id: str
    media_id: str
    media_type: str  # 'image' | 'video' | 'text' | 'poll'
    caption: str
    expires_at: str  # ISO 8601
    view_count: int
    created_at: str  # ISO 8601
    audience: str  # 'all' | 'selected' | 'excluded'
    audience_user_ids: list[str] | None = None
    author_name: str | None = None
    author_avatar: str | None = None
    viewed_by_me: bool = False
    media_url: str | None = None


@dataclass
class StoryView:
    story_id: str
    viewer_id: str
    viewed_at: str  # ISO 8601
    viewer_name: str | None = None
    viewer_avatar: str | None = None


@dataclass
class StoryMediaUpload:
    media_id: str
    url: str
    width: int | None = None
    height: int | None = None
    thumbnail_url: str | None = None
    medium_url: str | None = None


@dataclass
class StoryPreferences:
    audience: str
    audience_user_ids: list[str]


@dataclass
class StoryActionResult:
    done: bool = False


# ─── Parsers ──────────────────────────────────────────────────────────────────


def _story(d: dict[str, Any]) -> Story:
    d = d or {}
    return Story(
        id=str(d.get('id', '')),
        user_id=str(d.get('user_id', '')),
        media_id=str(d.get('media_id', '')),
        media_type=str(d.get('media_type', '')),
        caption=str(d.get('caption', '')),
        expires_at=str(d.get('expires_at', '')),
        view_count=int(d.get('view_count', 0)),
        created_at=str(d.get('created_at', '')),
        audience=str(d.get('audience', 'all')),
        audience_user_ids=d.get('audience_user_ids'),
        author_name=d.get('author_name'),
        author_avatar=d.get('author_avatar'),
        viewed_by_me=bool(d.get('viewed_by_me', False)),
        media_url=d.get('media_url'),
    )


def _view(d: dict[str, Any]) -> StoryView:
    return StoryView(
        story_id=str(d.get('story_id', '')),
        viewer_id=str(d.get('viewer_id', '')),
        viewed_at=str(d.get('viewed_at', '')),
        viewer_name=d.get('viewer_name'),
        viewer_avatar=d.get('viewer_avatar'),
    )


def _media_upload(d: dict[str, Any]) -> StoryMediaUpload:
    d = d or {}
    return StoryMediaUpload(
        media_id=str(d.get('media_id', '')),
        url=str(d.get('url', '')),
        width=d.get('width'),
        height=d.get('height'),
        thumbnail_url=d.get('thumbnail_url'),
        medium_url=d.get('medium_url'),
    )


def _prefs(d: dict[str, Any]) -> StoryPreferences:
    d = d or {}
    return StoryPreferences(
        audience=str(d.get('audience', 'all')),
        audience_user_ids=list(d.get('audience_user_ids') or []),
    )


def _action(d: Any) -> StoryActionResult:
    return StoryActionResult(done=bool((d or {}).get('done', False)))


class StoriesResource:
    """``me.stories`` — création et gestion des stories (utilisateur uniquement)."""

    def __init__(self, http: HttpClient, base: str) -> None:
        self._http = http
        self._base = base

    async def create(
        self,
        *,
        type: str,
        media: FileInput | None = None,
        media_id: str | None = None,
        caption: str | None = None,
        link: str | None = None,
        link_label: str | None = None,
        audience: str | None = None,
        audience_user_ids: list[str] | None = None,
    ) -> Story:
        """Créer une story.

        Pour ``image``/``video`` : passer ``media`` (uploadé automatiquement) ou
        un ``media_id`` déjà uploadé. Pour ``text``/``poll`` : juste ``caption``.

        Args:
            type:              'image' | 'video' | 'text' | 'poll'.
            media:             Fichier image/vidéo (bytes, file-like, ou FileData) — uploadé auto.
            media_id:          Alternative à ``media`` : un media_id déjà uploadé.
            caption:           Légende.
            link:              Lien CTA cliquable affiché sur la story par les apps Kappela.
                               Encodé dans la caption en JSON ({text, link, linkLabel}).
            link_label:        Libellé optionnel du lien CTA (ex. "Voir"). Nécessite ``link``.
            audience:          'all' (défaut) | 'selected' | 'excluded'.
            audience_user_ids: Requis si ``audience`` vaut 'selected' ou 'excluded'.
        """
        mid = media_id
        if type in ('image', 'video') and not mid:
            if media is None:
                raise ValueError("create: 'media' or 'media_id' is required for image/video stories")
            uploaded = await self.upload_media(media)
            mid = uploaded.media_id
        body: dict[str, Any] = {'media_type': type}
        if mid:
            body['media_id'] = mid
        cap = caption
        if link:
            # Le lien CTA est porté dans la caption en JSON ({text, link, linkLabel}) —
            # format lu par les apps Kappela (pas de champ backend dédié).
            env = {'text': caption or '', 'link': link}
            if link_label:
                env['linkLabel'] = link_label
            cap = json.dumps(env, ensure_ascii=False)
        if cap is not None:
            body['caption'] = cap
        if audience is not None:
            body['audience'] = audience
        if audience_user_ids is not None:
            body['audience_user_ids'] = audience_user_ids
        return _story(await self._http.post_json(f'{self._base}/createStory', body))

    async def upload_media(self, file: FileInput) -> StoryMediaUpload:
        """Uploader le média d'une story (image/vidéo) et retourner son media_id.

        Généralement inutile d'appeler directement — ``create(media=...)`` le fait.
        """
        raw = await self._http.post_multipart(f'{self._base}/uploadStoryMedia', {}, 'file', file)
        return _media_upload(raw)

    async def list(self) -> list[Story]:
        """Feed des stories actives de vos contacts."""
        raw = await self._http.post_json(f'{self._base}/getStories', {})
        return [_story(s) for s in (raw or [])]

    async def list_mine(self) -> list[Story]:
        """Vos propres stories."""
        raw = await self._http.post_json(f'{self._base}/getMyStories', {})
        return [_story(s) for s in (raw or [])]

    async def get(self, story_id: str) -> Story:
        """Une story par id (audience vérifiée côté serveur)."""
        return _story(await self._http.post_json(f'{self._base}/getStory', {'story_id': story_id}))

    async def delete(self, story_id: str) -> StoryActionResult:
        """Supprimer une de vos stories."""
        return _action(await self._http.post_json(f'{self._base}/deleteStory', {'story_id': story_id}))

    async def view(self, story_id: str) -> StoryActionResult:
        """Marquer une story comme vue."""
        return _action(await self._http.post_json(f'{self._base}/viewStory', {'story_id': story_id}))

    async def get_viewers(self, story_id: str) -> list[StoryView]:
        """Lister qui a vu une de vos stories (propriétaire uniquement)."""
        raw = await self._http.post_json(f'{self._base}/getStoryViewers', {'story_id': story_id})
        return [_view(v) for v in (raw or [])]

    async def get_preferences(self) -> StoryPreferences:
        """Préférence d'audience par défaut."""
        return _prefs(await self._http.post_json(f'{self._base}/getStoryPreferences', {}))

    async def set_preferences(self, audience: str, audience_user_ids: list[str] | None = None) -> StoryActionResult:
        """Définir la préférence d'audience par défaut."""
        body: dict[str, Any] = {'audience': audience}
        if audience_user_ids is not None:
            body['audience_user_ids'] = audience_user_ids
        return _action(await self._http.post_json(f'{self._base}/setStoryPreferences', body))
