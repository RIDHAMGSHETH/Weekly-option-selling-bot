"""
===============================================================================
LIVE NIFTY OPTION SELLING DASHBOARD & EXECUTION MONITOR
===============================================================================
Connects to Kotak Neo Live Stream:
- Shows Live NIFTY Spot Price & Session High/Low
- Shows Active Iron Condor Strikes & Real-Time Option Premiums
- Shows Live Unrealized P&L (Points & Rupees)
- Tracks 25% Stop-Loss thresholds, Trailing Cost Locks, and Target
- Updates terminal in real time every second with ANSI formatting
===============================================================================
"""

import os
import sys
import time
from datetime import datetime

BOT_DIR = os.path.dirname(__file__)
KOTAK_DIR = r"C:\Users\Ridham\.gemini\antigravity-ide\scratch\Kotak-neo-api-v2"

for p in [BOT_DIR, KOTAK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

from nifty_weekly_option_selling_bot import NiftyWeeklyOptionSellingBot

def run_live_terminal():
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.CYAN + "═" * 80)
    print(Fore.CYAN + Style.BRIGHT + "   ⚡ KOTAK NEO - LIVE NIFTY 0-DTE / WEEKLY OPTION SELLING MONITOR ⚡")
    print(Fore.CYAN + "═" * 80)
    print(Fore.YELLOW + "[*] Authenticating with Kotak Neo API...")
    
    bot = NiftyWeeklyOptionSellingBot(mode="PAPER")
    bot.initialize_market_connection()

    print(Fore.GREEN + "[+] Connected! Entering live trading session...\n")
    time.sleep(1)

    # Initial Entry if no position exists
    if not bot.active_position:
        print(Fore.YELLOW + "[*] Taking Live Market Entry Basket for Today...")
        bot.execute_basket_entry()
        time.sleep(1)

    print(Fore.GREEN + "\n[+] Live Execution Active. Launching Real-Time Terminal HUD...\n")
    time.sleep(1)

    try:
        while bot.running and bot.active_position:
            pos = bot.active_position
            spot = bot.get_spot_price()

            # Query current prices of the active legs
            reqs = []
            if pos["ce_token"]: reqs.append({"instrument_token": pos["ce_token"], "exchange_segment": "nse_fo"})
            if pos["pe_token"]: reqs.append({"instrument_token": pos["pe_token"], "exchange_segment": "nse_fo"})

            quotes = bot.client.quotes(instrument_tokens=reqs)
            cur_ce_px = pos["ce_entry"]
            cur_pe_px = pos["pe_entry"]

            if isinstance(quotes, list):
                for q in quotes:
                    tok = str(q.get("exchange_token") or q.get("instrument_token") or "")
                    ltp = float(q.get("ltp", 0.0) or q.get("last_price", 0.0))
                    if tok == pos["ce_token"] and ltp > 0: cur_ce_px = ltp
                    elif tok == pos["pe_token"] and ltp > 0: cur_pe_px = ltp

            # Evaluate stop losses and targets
            bot.monitor_tick()

            # P&L Calculation
            ce_decay = pos["ce_entry"] - (pos["ce_sl"] if pos["ce_stopped"] else cur_ce_px)
            pe_decay = pos["pe_entry"] - (pos["pe_sl"] if pos["pe_stopped"] else cur_pe_px)
            net_pts = ce_decay + pe_decay - (pos["wings_cost"] * 0.8)
            gross_pnl = net_pts * bot.config["lot_size"] * bot.config["lots"]

            pnl_color = Fore.GREEN if gross_pnl >= 0 else Fore.RED
            now_str = datetime.now().strftime("%H:%M:%S")

            # Render Screen HUD
            os.system("cls" if os.name == "nt" else "clear")
            print(Fore.CYAN + "═" * 80)
            print(Fore.CYAN + Style.BRIGHT + f"   NIFTY OPTION SELLING LIVE MONITOR  |  TIME: {now_str}  |  MODE: {pos.get('mode', bot.mode)}")
            print(Fore.CYAN + "═" * 80)

            # Spot Bar
            print(f" NIFTY 50 SPOT : {Style.BRIGHT}{Fore.WHITE}₹{spot:,.2f}   " +
                  f"| Capital : ₹{55000 * bot.config['lots']:,}   | Lots : {bot.config['lots']} ({bot.config['lot_size']} qty)")
            print(Fore.CYAN + "─" * 80)

            # Leg Breakdown Table
            print(f" {'LEG':<8} | {'STRIKE':<14} | {'ENTRY':<9} | {'CURRENT':<9} | {'STOP LOSS':<11} | {'DECAY (PTS)':<12} | {'STATUS':<10}")
            print(Fore.CYAN + "─" * 80)

            # CE Leg
            ce_status = Fore.RED + "STOPPED" if pos["ce_stopped"] else Fore.GREEN + "ACTIVE"
            print(f" {'SHORT CE':<8} | {pos['contracts']['short_ce']['trd_symbol']:<14} | "
                  f"₹{pos['ce_entry']:<8.2f} | ₹{cur_ce_px:<8.2f} | ₹{pos['ce_sl']:<10.2f} | "
                  f"{ce_decay:<+12.2f} | {ce_status}")

            # PE Leg
            pe_status = Fore.RED + "STOPPED" if pos["pe_stopped"] else Fore.GREEN + "ACTIVE"
            print(f" {'SHORT PE':<8} | {pos['contracts']['short_pe']['trd_symbol']:<14} | "
                  f"₹{pos['pe_entry']:<8.2f} | ₹{cur_pe_px:<8.2f} | ₹{pos['pe_sl']:<10.2f} | "
                  f"{pe_decay:<+12.2f} | {pe_status}")

            # Wings
            print(Fore.YELLOW + f" {'WINGS':<8} | {pos['contracts']['wing_ce']['strike']}CE / {pos['contracts']['wing_pe']['strike']}PE  | Cost: ₹{pos['wings_cost']:.2f} (Hedge margin unlocked 60%)")
            print(Fore.CYAN + "─" * 80)

            # Real-time Total P&L Box
            print(f" TOTAL UNREALIZED P&L : {Style.BRIGHT}{pnl_color}{gross_pnl:+,.2f} INR  ({net_pts:+.2f} points)")
            print(f" TARGET MILESTONE     : +₹{bot.config['profit_target_rs']:,.0f}  |  SQUARE OFF TIME : 13:30:00")
            print(Fore.CYAN + "═" * 80)
            print(Fore.LIGHTBLACK_EX + " [Ctrl + C to Stop Monitoring / Exit Trade Early]\n")

            time.sleep(1.0)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] User interrupted live monitor.")
        choice = input("Do you want to square-off the position now? (y/n): ").strip().lower()
        if choice == "y":
            bot.square_off(reason="MANUAL_EARLY_EXIT")
            print(Fore.GREEN + "[OK] Position squared off.")
        else:
            print(Fore.YELLOW + "[*] Leaving position active.")

if __name__ == "__main__":
    run_live_terminal()
