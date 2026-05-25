"""
Whale Tracker — monitors wallets on-chain for large buys/sells
"""
import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from config import (
    WHALE_WALLETS_FILE, DATA_DIR,
    WHALE_BUY_THRESHOLD_USD, WHALE_SELL_THRESHOLD_USD,
    WHALE_CHECK_INTERVAL_SECONDS, RPC_ENDPOINTS
)

logger = logging.getLogger(__name__)


def load_wallets():
    if os.path.exists(WHALE_WALLETS_FILE):
        with open(WHALE_WALLETS_FILE) as f:
            return json.load(f)
    return {}


def save_wallets(wallets):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(WHALE_WALLETS_FILE, "w") as f:
        json.dump(wallets, f, indent=2)


class WhaleTracker:
    def __init__(self, notifier):
        self.notifier = notifier
        self.wallets = load_wallets()  # {address: {chain, label, last_sig}}
        self.running = True
        self.check_count = 0

    def add_wallet(self, address, chain, label=""):
        self.wallets[address] = {
            "chain": chain.lower(),
            "label": label or address[:8] + "...",
            "last_tx": None,
            "added_at": datetime.utcnow().isoformat(),
        }
        save_wallets(self.wallets)

    def remove_wallet(self, address):
        removed = self.wallets.pop(address, None)
        save_wallets(self.wallets)
        return removed is not None

    def list_wallets(self):
        return self.wallets

    async def run_loop(self):
        logger.info(f"WhaleTracker started — watching {len(self.wallets)} wallets")
        while self.running:
            try:
                if self.wallets:
                    await self.check_all()
            except Exception as e:
                logger.error(f"WhaleTracker error: {e}")
            await asyncio.sleep(WHALE_CHECK_INTERVAL_SECONDS)

    async def check_all(self):
        self.check_count += 1
        tasks = [self.check_wallet(addr, info) for addr, info in list(self.wallets.items())]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def check_wallet(self, address, info):
        chain = info.get("chain", "solana")
        try:
            if chain == "solana":
                await self._check_solana(address, info)
            else:
                await self._check_evm(address, info, chain)
        except Exception as e:
            logger.debug(f"Wallet check error {address[:8]}: {e}")

    async def _check_solana(self, address, info):
        """Check Solana wallet via public RPC for recent transactions"""
        rpc = RPC_ENDPOINTS["solana"]
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": 5}]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
                sigs = data.get("result", [])
                if not sigs:
                    return

                latest_sig = sigs[0]["signature"]
                last_known = info.get("last_tx")

                if last_known is None:
                    # First run — just store the latest sig, don't alert
                    self.wallets[address]["last_tx"] = latest_sig
                    save_wallets(self.wallets)
                    return

                if latest_sig == last_known:
                    return  # No new txs

                # New transactions found
                new_sigs = []
                for sig_info in sigs:
                    if sig_info["signature"] == last_known:
                        break
                    new_sigs.append(sig_info["signature"])

                self.wallets[address]["last_tx"] = latest_sig
                save_wallets(self.wallets)

                for sig in new_sigs[:3]:  # process up to 3 new txs
                    await self._fetch_and_notify_solana_tx(sig, address, info, session)

    async def _fetch_and_notify_solana_tx(self, sig, address, info, session):
        """Fetch tx details and notify if it looks like a swap"""
        rpc = RPC_ENDPOINTS["solana"]
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getTransaction",
            "params": [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        }
        try:
            async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
                tx = data.get("result")
                if not tx:
                    return

                meta = tx.get("meta", {})
                pre_balances = meta.get("preBalances", [])
                post_balances = meta.get("postBalances", [])

                if pre_balances and post_balances:
                    sol_change = (post_balances[0] - pre_balances[0]) / 1e9
                    usd_estimate = abs(sol_change) * 150  # rough SOL price estimate

                    if usd_estimate >= WHALE_BUY_THRESHOLD_USD:
                        action = "🟢 BUY" if sol_change < 0 else "🔴 SELL"
                        await self.notifier.notify_whale_move({
                            "label": info.get("label", address[:8]),
                            "address": address,
                            "chain": "solana",
                            "action": action,
                            "usd_value": usd_estimate,
                            "sol_change": sol_change,
                            "sig": sig,
                        })
        except Exception as e:
            logger.debug(f"TX fetch error: {e}")

    async def _check_evm(self, address, info, chain):
        """Check EVM wallet via etherscan-compatible APIs (free tier)"""
        api_urls = {
            "ethereum": f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey=YourApiKeyToken",
            "bsc": f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc",
            "base": f"https://api.basescan.org/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc",
        }
        url = api_urls.get(chain)
        if not url:
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
                txs = data.get("result", [])
                if not isinstance(txs, list) or not txs:
                    return

                latest_hash = txs[0].get("hash")
                last_known = info.get("last_tx")

                if last_known is None:
                    self.wallets[address]["last_tx"] = latest_hash
                    save_wallets(self.wallets)
                    return

                if latest_hash == last_known:
                    return

                self.wallets[address]["last_tx"] = latest_hash
                save_wallets(self.wallets)

                for tx in txs:
                    if tx.get("hash") == last_known:
                        break
                    value_eth = int(tx.get("value", 0)) / 1e18
                    usd_est = value_eth * 3000  # rough ETH price
                    if usd_est >= WHALE_BUY_THRESHOLD_USD:
                        action = "🟢 BUY" if tx.get("to", "").lower() != address.lower() else "🔴 SELL"
                        await self.notifier.notify_whale_move({
                            "label": info.get("label", address[:8]),
                            "address": address,
                            "chain": chain,
                            "action": action,
                            "usd_value": usd_est,
                            "sig": tx.get("hash"),
                        })

    def get_stats(self):
        return {
            "wallet_count": len(self.wallets),
            "check_count": self.check_count,
        }
