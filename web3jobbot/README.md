# 🚀 Web3 Job Hunter Bot

A Telegram bot that scans new crypto projects and helps you land Web3 roles as a **Community Manager, Moderator, KOL, Raider, or Marketer**.

---

## 🌟 What It Does

| Feature | Details |
|---|---|
| 🔍 Token Scanner | Polls DexScreener every 60s for new tokens with socials |
| 💼 Job Detector | Auto-detects what roles a new project likely needs |
| 🐋 Whale Tracker | Monitors wallets on Solana, ETH, BSC, Base for big moves |
| 📲 Real-time Alerts | Instant Telegram notifications |
| ⛓️ Multi-chain | Solana, Ethereum, BSC, Base, Arbitrum |

---

## ⚙️ Setup (Step by Step)

### Step 1 — Get your Telegram Bot Token
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the steps
3. Copy the token it gives you (looks like `123456:ABCdef...`)

### Step 2 — Get your Chat ID
1. Search for **@userinfobot** on Telegram
2. Send `/start` — it will reply with your ID number

### Step 3 — Install Python
Download from https://python.org (3.10+ recommended)

### Step 4 — Run the bot

**Windows:**
```
1. Open the web3jobbot folder
2. Double-click run.sh (or open terminal and type: bash run.sh)
```

**Mac / Linux:**
```bash
cd web3jobbot
bash run.sh
```

The script will:
- Create a virtual environment
- Install all dependencies
- Create your `.env` file
- Ask you to fill in your tokens, then start the bot

### Step 5 — Fill in .env
Open the `.env` file and set:
```
BOT_TOKEN=paste_your_bot_token_here
CHAT_ID=paste_your_chat_id_here
```

Run `bash run.sh` again — the bot starts! 🎉

---

## 📱 Bot Commands

| Command | What it does |
|---|---|
| `/start` | Welcome screen with quick buttons |
| `/scan` | Manually trigger a token scan right now |
| `/setmcap 10000` | Set minimum MCap filter (default: $4,000) |
| `/alertson` | Enable real-time alerts |
| `/alertsoff` | Pause alerts |
| `/trackwhale [address] [chain] [label]` | Track a whale wallet |
| `/untrackwhale [address]` | Stop tracking a wallet |
| `/whales` | List all tracked wallets |
| `/status` | Bot stats and settings |
| `/help` | Full command list |

---

## 🐋 Whale Tracking Examples

```
/trackwhale 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM solana BigSolPlayer
/trackwhale 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 ethereum VitalikWallet
/trackwhale 0xF977814e90dA44bFA03b6295A0616a897441aceE bsc BinanceHotWallet
```

---

## 💼 How to Use This for Job Hunting

When you get a new token alert:

1. **Go to their Twitter** — Reply to their posts, be helpful and visible
2. **Join their Telegram** — Be one of the first members, greet people
3. **Join their Discord** — Engage in every channel early
4. **DM the founder** — Offer your skills: "I'm an experienced CM/mod, I'd love to help grow this project"
5. **Show your value first** — Share their posts, raid for them before being hired

> 🔑 **Key insight**: New projects post their socials first, hire later. Being early = being noticed.

---

## 📁 File Structure

```
web3jobbot/
├── main.py              # Bot entry point
├── config.py            # All settings
├── requirements.txt     # Python packages
├── run.sh               # One-click start script
├── .env.example         # Config template
├── .env                 # Your actual config (never share this!)
├── modules/
│   ├── scanner.py       # DexScreener token scanner
│   ├── whale_tracker.py # On-chain wallet monitor
│   ├── notifier.py      # Telegram message formatter
│   └── commands.py      # All /command handlers
├── data/                # Local database (JSON files)
│   ├── seen_tokens.json # Tokens already alerted
│   └── whale_wallets.json # Your tracked wallets
└── logs/
    └── bot.log          # Bot activity log
```

---

## 🔧 Customization

Edit `.env` to tune the bot:

```env
MIN_MCAP_USD=4000          # Lower = more alerts, higher = more selective
SCAN_INTERVAL_SECONDS=60   # How often to scan (don't go below 30)
WHALE_BUY_THRESHOLD_USD=10000  # Minimum USD move to alert on
```

---

## ⚠️ Notes

- **Free RPCs** are used by default — they may be slow at peak times. For better reliability, get a free key from Helius (Solana) or Alchemy (EVM)
- **X/Twitter API** is expensive ($100+/month), so this bot uses DexScreener's social links instead — projects always post their Twitter there
- The bot runs locally on your PC — keep it running for continuous alerts
- Data is saved locally in the `data/` folder

---

## 🆙 Future Upgrades (ask Claude!)

- Add Pump.fun direct API scanning
- Add automatic Twitter/X DM drafting
- Add job board scraping (crypto job sites)
- Pump.fun graduation alerts (token leaves pump = new project launching)
- Port to a free cloud host (Railway, Render) to run 24/7
