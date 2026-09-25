"""
===============================================================================
AUTONOMOUS NIFTY & SENSEX DUAL IRON CONDOR SCHEDULER & GITHUB SYNC
===============================================================================
Features:
1. Holiday-Aware: Checks official 2026 NSE/BSE Trading Calendar before starting
   (Skips weekends, NSE/BSE designated holidays)
2. Dual Index Execution:
   - NIFTY 50 (Tue, Wed, Thu) & BSE SENSEX (Thu, Fri) or simultaneous dual runs
3. Strategy Rules:
   - 09:25 AM: Dynamically resolves +-0.6% OTM Short Strangle + Wings & enters basket
   - 09:25 AM - 13:30 PM: High-speed monitoring of independent 25% SL per leg & +Rs 3k Target
   - 13:30 PM: Automated early theta decay square-off
   - 15:30 PM: Auto-commits and pushes updated Trading Journal & Ledger to GitHub
4. Explicit SL Trailing Rule:
   - If one leg stops out, the surviving leg maintains its standard 25% SL (no cost trail).
5. Telegram Integration: Dispatches startup, entry, SL events, and daily PnL summaries.
===============================================================================
"""

import os
import sys
import time
import subprocess
from datetime import datetime, time as dtime

BOT_DIR = os.path.dirname(__file__)
KOTAK_DIR = r"C:\Users\Ridham\.gemini\antigravity-ide\scratch\Kotak-neo-api-v2"

for p in [BOT_DIR, KOTAK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from trading_calendar import get_market_status, is_weekend, HOLIDAYS_2026
from nifty_weekly_option_selling_bot import MultiIndexIronCondorBot

def sync_journal_to_github():
    """Commits and pushes the markdown journal & CSV to GitHub."""
    print("[*] Syncing Trading Journal to GitHub...")
    try:
        subprocess.run("git add -A", cwd=BOT_DIR, shell=True, check=True)
        commit_msg = f"Auto-journal trade update for {datetime.now().strftime('%Y-%m-%d')}"
        res = subprocess.run(f'git commit -m "{commit_msg}"', cwd=BOT_DIR, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "nothing to commit" in res.stdout or "nothing to commit" in res.stderr:
            print("[+] Working tree clean. Nothing new to commit.")
            return True
        push_res = subprocess.run("git push origin main", cwd=BOT_DIR, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if push_res.returncode == 0:
            print("[OK] Successfully pushed trading journal to GitHub!")
            return True
        else:
            print(f"[-] Push notification: {push_res.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[-] Git sync error: {e}")
        return False

class DualIndexOptionSellingScheduler:
    def __init__(self, symbols=None, check_interval_sec=15):
        self.symbols = symbols or ["NIFTY", "SENSEX"]
        self.check_interval_sec = check_interval_sec
        self.bots = {}
        self.entered_today = {sym: False for sym in self.symbols}
        self.squared_off_today = {sym: False for sym in self.symbols}
        self.current_trading_date = None

    def run_daily_cycle(self):
        print("="*80)
        print("   AUTONOMOUS DUAL INDEX (NIFTY & SENSEX) IRON CONDOR SCHEDULER")
        print("   Target: https://github.com/RIDHAMGSHETH/Weekly-option-selling-bot.git")
        print(f"   Symbols: {', '.join(self.symbols)}")
        print("   Enforcing: Mon-Fri Only | Official 2026 Holidays | 09:25 -> 13:30 Window")
        print("   Risk Rule: Independent 25% SL per leg (cost-trailing disabled)")
        print("="*80 + "\n")

        while True:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            now_time = now.time()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")

            # Date reset
            if self.current_trading_date != today_str:
                self.current_trading_date = today_str
                self.entered_today = {sym: False for sym in self.symbols}
                self.squared_off_today = {sym: False for sym in self.symbols}
                self.bots = {}

            # 1. Check Market Status
            status = get_market_status(now)

            if not status["is_trading_day"] or (HOLIDAYS_2026.get(today_str) and HOLIDAYS_2026[today_str].get("nse_closed")):
                reason = status.get("reason", "Holiday")
                print(f"\r[{now_str}] Market Inactive. Reason: {reason} | Bot sleeping...", end="", flush=True)
                time.sleep(self.check_interval_sec)
                continue

            # 2. Market Open Check (09:15 to 15:30)
            if not status["nse_open"]:
                print(f"\r[{now_str}] Market Closed right now ({status['reason']}) | Bot standby...", end="", flush=True)
                time.sleep(self.check_interval_sec)
                continue

            # 3. Initialize bot connections
            for sym in self.symbols:
                if sym not in self.bots:
                    try:
                        print(f"\n[{now_str}] Market Open. Initializing {sym} Iron Condor Engine...")
                        bot = MultiIndexIronCondorBot(symbol=sym, mode="PAPER")
                        bot.initialize_market_connection()
                        self.bots[sym] = bot
                    except Exception as e:
                        print(f"[-] {sym} Bot init error: {e}")

            # 4. Entry Window: Trigger exactly at 09:25 AM
            entry_time_obj = dtime(9, 25)
            square_off_time_obj = dtime(13, 30)

            for sym, bot in self.bots.items():
                if now_time >= entry_time_obj and not self.entered_today[sym] and not self.squared_off_today[sym]:
                    print(f"\n[{now_str}] Entry Window Reached (>= 09:25 AM). Executing {sym} Basket...")
                    try:
                        bot.execute_basket_entry()
                        self.entered_today[sym] = True
                    except Exception as e:
                        print(f"[-] {sym} Basket entry error: {e}")

            # 5. Position Active Monitoring & Square-Off
            any_squared_off = False
            for sym, bot in self.bots.items():
                if bot and bot.active_position:
                    bot.monitor_tick()

                    # Check 13:30 PM Square-off
                    if now_time >= square_off_time_obj and not self.squared_off_today[sym]:
                        print(f"\n[{now_str}] 13:30 PM Time Window Reached. Squaring off {sym} positions...")
                        bot.square_off(reason="SCHEDULED_1330_THETA_EXIT")
                        self.squared_off_today[sym] = True
                        any_squared_off = True

            if any_squared_off:
                sync_journal_to_github()

            time.sleep(self.check_interval_sec)

if __name__ == "__main__":
    scheduler = DualIndexOptionSellingScheduler(symbols=["NIFTY", "SENSEX"], check_interval_sec=10)
    scheduler.run_daily_cycle()
