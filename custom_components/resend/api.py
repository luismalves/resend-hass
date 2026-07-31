"""Minimal Resend REST client.

ponytail: sending an email is one POST, so this uses Home Assistant's shared
aiohttp session instead of the official ``resend`` SDK — that SDK is sync-only
and every call would need wrapping in an executor job.
"""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

API_URL = "https://api.resend.com/emails"


class ResendError(Exception):
    """Resend rejected the request or was unreachable."""


class InvalidAuth(ResendError):
    """The API key was rejected."""


class CannotConnect(ResendError):
    """Resend could not be reached."""


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


async def async_send(
    session: ClientSession, api_key: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Send one email and return Resend's response body."""
    try:
        resp = await session.post(API_URL, json=payload, headers=_headers(api_key))
        body = await resp.json(content_type=None)
    except (ClientError, TimeoutError) as err:
        raise CannotConnect(f"Could not reach Resend: {err}") from err

    if resp.status >= 400:
        detail = body.get("message", body) if isinstance(body, dict) else body
        if resp.status in (401, 403):
            raise InvalidAuth(f"Resend rejected the API key: {detail}")
        raise ResendError(f"Resend rejected the email ({resp.status}): {detail}")

    return body if isinstance(body, dict) else {}


async def async_validate_key(session: ClientSession, api_key: str) -> None:
    """Check an API key without sending anything.

    ponytail: an empty POST is the only probe a sending-only key can pass —
    GET /domains returns 401 for restricted keys, so it can't tell a valid
    sending key from a bad one. 401/403 here means bad key, 422 means it works.
    """
    try:
        resp = await session.post(API_URL, json={}, headers=_headers(api_key))
    except (ClientError, TimeoutError) as err:
        raise CannotConnect(str(err)) from err

    if resp.status in (401, 403):
        raise InvalidAuth
