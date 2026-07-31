"""Map Home Assistant service data onto the Resend ``POST /emails`` body.

Kept free of Home Assistant and aiohttp imports so ``tests/test_payload.py``
runs with nothing installed.
"""

from __future__ import annotations

from typing import Any

# Fields that pass through to the Resend API unchanged.
PASSTHROUGH = (
    "subject",
    "html",
    "text",
    "cc",
    "bcc",
    "reply_to",
    "headers",
    "tags",
    "attachments",
    "scheduled_at",
)


def build_payload(data: dict[str, Any], default_from: str) -> dict[str, Any]:
    """Build the Resend request body.

    ``from_address`` falls back to the config entry's sender. ``template_id``
    and ``template_variables`` are folded into Resend's nested ``template``
    object. Resend itself rejects template + html/text and missing subjects,
    so we don't duplicate those rules here.
    """
    payload: dict[str, Any] = {
        "from": data.get("from_address") or default_from,
        "to": data["to"],
    }

    for key in PASSTHROUGH:
        if (value := data.get(key)) is not None:
            payload[key] = value

    if template_id := data.get("template_id"):
        payload["template"] = {"id": template_id}
        if variables := data.get("template_variables"):
            payload["template"]["variables"] = variables

    return payload
