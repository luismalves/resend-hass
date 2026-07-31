"""Check the Resend payload mapping. Run: python tests/test_payload.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "resend"))

from payload import build_payload  # noqa: E402

DEFAULT_FROM = "Home <ha@example.com>"


def test_template_is_nested():
    payload = build_payload(
        {
            "to": ["a@example.com"],
            "template_id": "garage-alert",
            "template_variables": {"DOOR": "Garage"},
        },
        DEFAULT_FROM,
    )
    assert payload["template"] == {"id": "garage-alert", "variables": {"DOOR": "Garage"}}
    assert "template_id" not in payload
    assert "template_variables" not in payload


def test_template_without_variables():
    payload = build_payload({"to": ["a@e.com"], "template_id": "x"}, DEFAULT_FROM)
    assert payload["template"] == {"id": "x"}


def test_from_defaults_and_overrides():
    assert build_payload({"to": ["a@e.com"]}, DEFAULT_FROM)["from"] == DEFAULT_FROM
    override = build_payload({"to": ["a@e.com"], "from_address": "b@e.com"}, DEFAULT_FROM)
    assert override["from"] == "b@e.com"


def test_only_supplied_fields_are_sent():
    payload = build_payload({"to": ["a@e.com"], "subject": "hi", "cc": []}, DEFAULT_FROM)
    assert payload == {"from": DEFAULT_FROM, "to": ["a@e.com"], "subject": "hi", "cc": []}
    assert "html" not in payload and "bcc" not in payload


def test_passthrough_fields():
    data = {
        "to": ["a@e.com"],
        "html": "<b>hi</b>",
        "bcc": ["c@e.com"],
        "reply_to": ["r@e.com"],
        "scheduled_at": "in 1 hour",
        "tags": [{"name": "kind", "value": "alert"}],
        "attachments": [{"filename": "x.jpg", "path": "https://e.com/x.jpg"}],
        "headers": {"X-A": "1"},
        # Not part of the API — must be dropped.
        "config_entry_id": "abc123",
    }
    payload = build_payload(data, DEFAULT_FROM)
    for key in ("html", "bcc", "reply_to", "scheduled_at", "tags", "attachments", "headers"):
        assert payload[key] == data[key], key
    assert "config_entry_id" not in payload


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all passed")
