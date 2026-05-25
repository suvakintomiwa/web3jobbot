"""
Bot Configuration — fill in your values in .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID_HERE")

# Multi-user: comma-separated chat IDs
# e.g. EXTRA_CHAT_IDS=123456789,987654321
_extra = os.getenv("EXTRA_CHAT_IDS", "")
EXTRA_CHAT_IDS = [x.strip() for x in _extra.split(",") if x.strip()]
ALL_CHAT_IDS = list(dict.fromkeys([CHAT_ID] + EXTRA_CHAT_IDS))  # dedupe, owner first

# Scanning settings
MIN_MCAP_USD = int(os.getenv("MIN_MCAP_USD", "4000"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))
WHALE_CHECK_INTERVAL_SECONDS = int(os.getenv("WHALE_CHECK_INTERVAL_SECONDS", "30"))
PUMPFUN_INTERVAL_SECONDS = int(os.getenv("PUMPFUN_INTERVAL_SECONDS", "30"))
JOB_SCAN_INTERVAL_SECONDS = int(os.getenv("JOB_SCAN_INTERVAL_SECONDS", "3600"))

# Chains to monitor on DexScreener
TARGET_CHAINS = ["solana", "ethereum", "bsc", "base", "arbitrum"]

# DexScreener API
DEXSCREENER_BASE = "https://api.dexscreener.com"
DEXSCREENER_LATEST = f"{DEXSCREENER_BASE}/token-profiles/latest/v1"
DEXSCREENER_NEW_PAIRS = f"{DEXSCREENER_BASE}/token-boosts/latest/v1"
DEXSCREENER_SEARCH = f"{DEXSCREENER_BASE}/latest/dex/search"
DEXSCREENER_PAIRS = f"{DEXSCREENER_BASE}/latest/dex/pairs"

# Pump.fun
PUMPFUN_API = "https://frontend-api.pump.fun/coins"
PUMPFUN_GRADUATING = "https://frontend-api.pump.fun/coins/graduating"

# Job boards
JOB_BOARDS = [
    "https://web3.career/community-manager-jobs",
    "https://web3.career/moderator-jobs",
    "https://web3.career/marketing-jobs",
    "https://cryptojobslist.com/community",
]

# RPC endpoints (free public nodes)
RPC_ENDPOINTS = {
    "solana": os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com"),
    "ethereum": os.getenv("ETH_RPC", "https://eth.llamarpc.com"),
    "bsc": os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org"),
    "base": os.getenv("BASE_RPC", "https://mainnet.base.org"),
}

# Whale tracking thresholds (USD)
WHALE_BUY_THRESHOLD_USD = int(os.getenv("WHALE_BUY_THRESHOLD_USD", "10000"))
WHALE_SELL_THRESHOLD_USD = int(os.getenv("WHALE_SELL_THRESHOLD_USD", "10000"))

# Data persistence
DATA_DIR = "data"
SEEN_TOKENS_FILE = f"{DATA_DIR}/seen_tokens.json"
SEEN_PUMPFUN_FILE = f"{DATA_DIR}/seen_pumpfun.json"
SEEN_JOBS_FILE = f"{DATA_DIR}/seen_jobs.json"
WHALE_WALLETS_FILE = f"{DATA_DIR}/whale_wallets.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"
STATS_FILE = f"{DATA_DIR}/stats.json"
