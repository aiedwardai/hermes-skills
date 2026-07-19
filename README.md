# Hermes Skills

This repository stores Hermes Agent skills under `skills/`.

## Included Skills

| Skill | Purpose |
|-------|---------|
| `fenghuang-fm` | Download, transcribe, and archive Fenghuang FM programs. |
| `hermes-tweet` | Search Twitter/X, read replies, monitor tweets, export followers, and keep X actions approval-gated through Hermes Tweet. |
| `shanyong-ai-intro-series` | Write practical AI tool tutorials in the Shanyong AI introduction style. |
| `vtts` | Generate speech with the Volcengine TTS V3 API. |
| `wordpress-auto-publisher` | Review and publish content through the WordPress REST API. |

## Hermes Tweet

Install the native plugin before using the `hermes-tweet` skill:

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
hermes tools list
```

Keep `XQUIK_API_KEY` in the Hermes runtime environment. Do not paste API keys,
passwords, cookies, or TOTP secrets into chat or tool arguments.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
