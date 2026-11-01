# 🤖 WorkflowAlpha AI Bot

AI-powered Telegram bot for image generation, AI chat, text-to-speech, and text processing.

## 🚀 Try It Now

**[@workflowalpha_earning_bot](https://t.me/workflowalpha_earning_bot)**

No app download needed. Works directly in Telegram.

## ✨ Features

- 🎨 **Image Generation** - Create stunning AI images from text descriptions using Pollinations AI
- 💬 **AI Chat** - Chat with our intelligent bot. Ask questions, get answers. **100% Free!**
- 🔊 **Text to Speech** - Convert any text up to 60 seconds into natural-sounding speech
- 📝 **Text Processing** - Convert case, reverse text, count characters/words. **Free forever!**

## 💰 Pricing

| Service | Price |
|---------|-------|
| 🎨 Image Generation | $0.25 per image |
| 💬 AI Chat | **Free** |
| 🔊 Text to Speech | $0.25 per audio |
| 📝 Text Processing | **Free** |

**Payment:** USDC on Base network  
**Wallet:** `0x37239...38C57`

## 🛠️ Tech Stack

- Python 3.14+
- python-telegram-bot
- Pollinations AI (free image generation)
- edge-tts (free text-to-speech)
- SQLite (revenue tracking)

## 📸 Demo

![Demo Screenshot](/tmp/demo_image_1.jpg)

*Example: AI-generated image via the bot*

## 🔧 Setup

1. Clone this repo
2. Install dependencies:
```bash
pip install python-telegram-bot requests pillow edge-tts
```
3. Create `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
HF_API_TOKEN=optional_hf_token
```
4. Run the bot:
```bash
python3 telegram_ai_bot.py
```

## 📝 Systemd Service

```ini
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/telegram-bot
ExecStart=/usr/bin/python3 /opt/telegram-bot/telegram_ai_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🌐 Live

- **Bot:** [@workflowalpha_earning_bot](https://t.me/workflowalpha_earning_bot)
- **Landing Page:** [https://workflowalpha.theworkpc.com/telegram-bot.html](https://workflowalpha.theworkpc.com/telegram-bot.html)
- **GitHub:** [https://github.com/Reggiebro/telegram-ai-bot](https://github.com/Reggiebro/telegram-ai-bot)

## 📧 Contact

For business inquiries: **workflowalpha.ai@gmail.com**

## 📄 License

MIT License - feel free to fork and modify!

---

Made with ❤️ by Workflow Alpha Team
