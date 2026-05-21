# Telegram Bot

A simple Python Telegram bot built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) that responds to the `/start` command.

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Your Telegram bot token from [@BotFather](https://t.me/BotFather) |

## Deployment on Railway

1. Fork or clone this repository.
2. Create a new Railway project and connect the repository.
3. Set the `TELEGRAM_TOKEN` environment variable in the Railway service settings.
4. Railway (via Railpack) will automatically detect Python, install dependencies from `requirements.txt`, and run `main.py`.

## Local Development

```bash
pip install -r requirements.txt
TELEGRAM_TOKEN=your_token_here python main.py
```
