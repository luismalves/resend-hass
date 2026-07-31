# Resend for Home Assistant

Send email from Home Assistant through [Resend](https://resend.com) — including
**Resend hosted templates**, which the built-in SMTP integration cannot do.

[![hacs][hacs-badge]][hacs]

## What you get

| Surface | Use it for |
| --- | --- |
| `notify.<your_sender>` entity | Plain-text alerts to a fixed recipient. Works anywhere HA takes a notify entity (automations, alerts, the mobile "notify" picker). |
| `resend.send_email` action | Everything else: templates + variables, HTML, CC/BCC, reply-to, attachments, tags, scheduled sends. Returns the Resend message ID. |

## Install

### HACS

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/luismalves/resend-hass`, category **Integration**.
2. Search for **Resend**, install, restart Home Assistant.

### Manual

Copy `custom_components/resend` into your `config/custom_components/` folder and restart.

## Set up

**Settings → Devices & Services → Add Integration → Resend.**

| Field | Notes |
| --- | --- |
| API key | From [resend.com/api-keys](https://resend.com/api-keys). *Sending access* is enough. |
| Sender address | Must be on a domain you verified in Resend. `Home Assistant <ha@example.com>` works. |
| Default recipients | Where the notify entity sends. `resend.send_email` can override per call. |

## Sending with a template

Publish a template in Resend, then reference it by ID or alias. Variable keys
allow letters, numbers and underscores; `FIRST_NAME`, `LAST_NAME`, `EMAIL` and
`UNSUBSCRIBE_URL` are reserved by Resend.

```yaml
action: resend.send_email
data:
  to: someone@example.com
  template_id: garage-alert
  template_variables:
    DOOR: Garage
    MINUTES: "20"
```

Subject, from and reply-to fall back to the template's defaults, and override
them when you pass them explicitly. Every variable the template references must
be supplied or Resend rejects the send.

### Without a template

```yaml
action: resend.send_email
data:
  to:
    - someone@example.com
    - other@example.com
  cc: manager@example.com
  subject: Washing machine finished
  html: "<b>Done</b> at {{ now().strftime('%H:%M') }}"
```

### Attachments and scheduling

```yaml
action: resend.send_email
data:
  to: someone@example.com
  subject: Daily summary
  text: Attached.
  scheduled_at: in 1 hour
  attachments:
    - filename: chart.png
      path: https://example.com/chart.png
```

Attachments take either `path` (a URL Resend fetches) or `content` (base64).

### Capturing the message ID

```yaml
action: resend.send_email
data:
  to: someone@example.com
  template_id: welcome
response_variable: sent
```

`sent.id` holds the Resend email ID.

### Notify entity

```yaml
action: notify.send_message
target:
  entity_id: notify.ha_example_com
data:
  title: Alarm triggered
  message: Motion in the hallway.
```

## Multiple Resend accounts

Add the integration once per sender address. `resend.send_email` then needs
`config_entry_id` to pick one; with a single account you can leave it out.

## Not included

- Local file attachments — pass base64 in `content`, or host the file and use `path`.
- Batch send, contacts/audiences, domain management.
- Editing an account after setup — remove and re-add it.

Open an issue if you want any of these.

## Development

```bash
python tests/test_payload.py
```

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
