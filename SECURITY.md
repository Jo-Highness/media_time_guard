# Security Policy

## Supported versions

Media Time Guard follows a **latest-only** support policy. Security fixes are
released against the most recent version. Please make sure you are running the
latest release before reporting an issue.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a vulnerability

Please report security issues **privately** through
[GitHub Security Advisories](https://github.com/Jo-Highness/media_time_guard/security/advisories/new).
Do not open a public issue for a security report.

We will acknowledge your report, investigate, and coordinate a fix and disclosure
with you.

## Scope and threat model

Media Time Guard is a **local-only** Home Assistant integration:

- It runs entirely inside your Home Assistant instance.
- It uses **no cloud services** and makes **no outbound network calls**.
- It **stores and requests no credentials, API keys or secrets**.

It interacts only with local `media_player` entities and Home Assistant's own
state. As such, the attack surface is limited to the local Home Assistant
environment. Reports about local logic errors, tamper-resistance bypasses or
unexpected data exposure within Home Assistant are still very welcome.
