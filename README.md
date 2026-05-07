# 🎙 Founder Notes Bot

A Telegram bot that turns YouTube podcasts & videos into **clean, structured notes** — powered by OpenRouter AI.

🤖 Bot: [@Founder_Note_bot](https://t.me/Founder_Note_bot)  
📢 Channel: [@foundernoteshappy](https://t.me/foundernoteshappy)

---

## 🚀 What It Does

Send a YouTube URL → Bot extracts the transcript → AI generates structured notes with:

| Section | What You Get |
|---------|-------------|
| 🎙 Title | Podcast/video title |
| 📌 Summary | 2–4 line quick overview |
| 💡 Key Takeaways & Insights | Main lessons and important ideas |
| 🛠 Tools / Systems Mentioned | Apps, workflows, automations, frameworks |
| ⚡ Actionable Ideas | Things worth applying |
| 🧠 Mindset Shifts | Important ways of thinking |

Notes are sent directly in Telegram **and** posted to your Founder Notes channel.

---

## 🗂 Project Structure

```
founder-notes-bot/
├── bot.py               # Telegram handlers, webhook & polling entry point
├── gemini_service.py    # OpenRouter AI integration & note generation
├── youtube_service.py   # YouTube URL validation & transcript extraction
├── prompts.py           # AI prompt templates
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── .env.example         # Environment variable template
├── .env                 # Your secrets (never commit this)
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/happyhaplu/founder-notes-bot.git
cd founder-notes-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values (see below).

---

## 🔑 API Keys

### Telegram Bot Token
1. Open Telegram → search `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the token into `.env`

### OpenRouter API Key
1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create a free account and generate a key
3. Copy into `.env`

---

## 📺 Channel Setup

To auto-post notes to your channel:
1. Create a Telegram channel
2. Add your bot as **Admin** with "Post Messages" permission
3. Set `CHANNEL_ID=@yourchannelname` in `.env`

---

## 💻 Running Locally

```bash
# Set RUN_MODE=polling in .env
python bot.py
```

You'll see:
```
Starting bot in POLLING mode...
```

Drop a YouTube link in your bot chat to test it.

---

## ☁️ Deploying to Render

### Step 1: Fork & push to GitHub

Make sure your repo is on GitHub (without `.env` — it's in `.gitignore`).

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Render auto-detects `render.yaml`
4. Set these environment variables in the Render dashboard:

| Variable | Value |
|----------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `CHANNEL_ID` | `@yourchannelname` |
| `WEBHOOK_URL` | `https://your-app.onrender.com` |
| `RUN_MODE` | `webhook` |

5. Click **Deploy**

The bot auto-registers the webhook on startup. The `/health` endpoint keeps the service alive on Render's free tier.

---

## 🛠 How It Works

```
User sends YouTube URL
        ↓
Validate URL & extract video ID
        ↓
Fetch transcript via youtube-transcript-api
(fallback: yt-dlp VTT parsing)
        ↓
Send transcript to OpenRouter AI with structured prompt
        ↓
AI returns formatted notes
        ↓
Bot sends notes to user
        ↓
Bot posts notes to Founder Notes channel
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `python-telegram-bot==21.6` | Telegram Bot API wrapper |
| `requests` | OpenRouter API calls |
| `youtube-transcript-api==1.2.4` | YouTube transcript extraction |
| `python-dotenv` | Load `.env` variables |
| `fastapi` + `uvicorn` | Webhook server for Render production |
| `httpx` | Async HTTP client |

---

## 🔒 Security

- Never commit `.env` to version control
- All secrets loaded via environment variables
- `.gitignore` excludes `.env`

---

## 📝 License

MIT — built for founder learning and productivity.
