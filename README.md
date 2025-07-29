# Telegram Bot Deployment on Render

Deploy Telegram bots on [Render](https://render.com/) with two ready-to-use implementations.
Partially based on the blog post [Getting your python telegram bot working on Render](https://dashdashhard.com/posts/python-telegram-bots/).

## Bot Options

- **`async_bot.py`** - Production-ready bot with webhooks (recommended for Render)
- **`sync_bot.py`** - Simple polling bot (for learning and local development)

## Quick Deploy

1. **Get bot token**: Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. **Fork this repo**: Click "Fork" button above
3. **Deploy on Render**:
   - New → Blueprint → Connect your fork
   - Add environment variable: `BOT_TOKEN=your_token_here`
   - Deploy

Your bot will be live at `https://your-app.onrender.com/healthcheck`
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/adaaaaaamenko/render_telegram_bot/)


## Why Webhooks on Render?

Render's health checks cause polling bots to fail with:

```
telegram.error.Conflict: terminated by other getUpdates request
```

The `async_bot.py` solves this by:

- Using webhooks in production (no polling conflicts)
- Providing `/healthcheck` endpoint for Render
- Auto-switching to polling for local development

### Alternative: Background Workers (Paid)

If you prefer using polling bots and don't mind paying, **Background Workers** are actually a better solution:

- **No health checks**: Background workers don't have HTTP health check requirements
- **Long-running processes**: Designed for bots that run continuously
- **Use any bot**: Both `async_bot.py` and `sync_bot.py` work without modification
- **Simpler setup**: No need for webhook configuration

**To use Background Workers:**
1. Deploy as a "Background Worker" instead of "Web Service"
2. Use either bot file with polling mode
3. No need for `/healthcheck` endpoint

**Trade-off**: Background workers cost money, while web services with webhooks can use the free tier.

## Local Development

```bash
pip install -r requirements.txt
BOT_TOKEN=your_token_here python async_bot.py  # Recommended
BOT_TOKEN=your_token_here python sync_bot.py   # Learning only
```

## Bot Comparison

| Feature               | async_bot.py    | sync_bot.py       |
| --------------------- | --------------- | ----------------- |
| **Render Free Tier**  | ✅ Works        | ❌ Conflicts      |
| **Local Development** | ✅ Auto-polling | ✅ Simple polling |
| **Production Ready**  | ✅ Webhooks     | ❌ Polling only   |
| **Best For**          | Deployment      | Learning          |

## Configuration Files

### `render.yaml` - Deployment Configuration

This file tells Render how to deploy your bot. It specifies:

- **Service type**: Web service with public URL
- **Runtime**: Python environment
- **Build process**: How to install dependencies
- **Start command**: Which bot file to run
- **Environment variables**: Bot token configuration

**To customize:**

- Change the service `name` to your preferred identifier
- Switch the `startCommand` to run `sync_bot.py` instead of `async_bot.py`
- Upgrade the `plan` from `free` to paid tiers for more resources
- Add additional environment variables if your bot needs them

### `requirements.txt` - Python Dependencies

Lists the Python packages your bot needs:

- **python-telegram-bot**: Main library for Telegram bot functionality
- **uvicorn**: ASGI server for handling webhooks
- **starlette**: Web framework for HTTP endpoints and health checks

**To customize:**

- Add new packages for additional bot features (databases, APIs, etc.)
- Update package versions (check compatibility with python-telegram-bot)
- Remove web-related packages (`uvicorn`, `starlette`) if only using sync bot locally
- Pin specific versions for reproducible deployments

## Resources

- [Original Blog Post](https://dashdashhard.com/posts/python-telegram-bots/) - Explains the Render deployment challenge
- [Render Docs](https://render.com/docs)
- [python-telegram-bot Docs](https://python-telegram-bot.readthedocs.io/)
