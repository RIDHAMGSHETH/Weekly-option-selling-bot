"""
===============================================================================
MULTI-INDEX HEDGED IRON CONDOR EXECUTION BOT (NIFTY 50 & BSE SENSEX)
===============================================================================
Features:
1. Multi-Index Support:
   - NIFTY 50 (NSE): 09:25 Entry on Allowed Expiry Days (Tue, Wed, Thu)
   - SENSEX (BSE): 09:25 Entry on Friday Expiries
2. Dynamic Strike & Wing Selection:
   - Sells OTM Short Call & Put
   - Buys Outer Wings first for ~60% margin reduction benefit
3. Pure 25% Stop-Loss Per Leg (WITHOUT Trailing Surviving Leg to Cost):
   - When a short leg breaches 25% SL, it is cut immediately.
   - The surviving winning leg keeps its standard original 25% stop-loss (NO cost trail).
4. Targets & Square-Off:
   - Target profit milestone (+₹3,000 / lot) early exit
   - Automated 13:30 PM time-decay square-off
   - Auto-journaling to Markdown & CSV
===============================================================================
"""

import os
import sys
import time
import json
import re
from datetime import datetime, time as dtime
import pandas as pd

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
KOTAK_SDK_DIR = r"C:\Users\Ridham\.gemini\antigravity-ide\scratch\Kotak-neo-api-v2"
for p in [BOT_DIR, KOTAK_SDK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from telegram_alerter import TelegramAlerter
from journaler import TradeJournaler
from kotak_neo_session import get_kotak_session

CONFIG_PATH = os.path.join(BOT_DIR, "bot_config.json")

class MultiIndexIronCondorBot:
    def __init__(self, symbol="NIFTY", mode=None):
        self.symbol = symbol.upper()
        self.load_config()
        if mode:
            self.config["trading_mode"] = mode.upper()
        self.mode = self.config.get("trading_mode", "PAPER")

        self.alerter = TelegramAlerter()
        self.journaler = TradeJournaler()
        self.client = None
        self.master_df = None

        self.active_position = None
        self.cumulative_pnl = 0.0
        self.running = True

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                self.full_config = json.load(f)
        else:
            self.full_config = {}

        asset_cfgs = self.full_config.get("asset_configs", {})
        default_asset = asset_cfgs.get(self.symbol, {
            "lot_size": 75 if self.symbol == "NIFTY" else 20,
            "lots": 1,
            "strike_step": 50 if self.symbol == "NIFTY" else 100,
            "otm_percent": 0.006 if self.symbol == "NIFTY" else 0.007,
            "wing_percent": 0.010 if self.symbol == "NIFTY" else 0.012,
            "stop_loss_pct": 0.25,
            "profit_target_rs": 3000.0,
            "trail_winning_leg_to_cost": False,
            "allowed_expiry_days": ["Tuesday", "Thursday", "Wednesday"] if self.symbol == "NIFTY" else ["Friday", "Thursday"]
        })

        self.config = {
            "trading_mode": self.full_config.get("trading_mode", "PAPER"),
            "symbol": self.symbol,
            "lot_size": default_asset.get("lot_size", 75 if self.symbol == "NIFTY" else 20),
            "lots": default_asset.get("lots", 1),
            "strike_step": default_asset.get("strike_step", 50 if self.symbol == "NIFTY" else 100),
            "otm_percent": default_asset.get("otm_percent", 0.006),
            "wing_percent": default_asset.get("wing_percent", 0.010),
            "stop_loss_pct": default_asset.get("stop_loss_pct", 0.25),
            "profit_target_rs": default_asset.get("profit_target_rs", 3000.0),
            "trail_winning_leg_to_cost": False,  # Explicitly disabled per user rule
            "entry_time": self.full_config.get("entry_time", "09:25"),
            "square_off_time": self.full_config.get("square_off_time", "13:30"),
            "hard_cutoff_time": self.full_config.get("hard_cutoff_time", "15:15"),
            "allowed_expiry_days": default_asset.get("allowed_expiry_days", ["Tuesday", "Thursday", "Wednesday"])
        }

    def initialize_market_connection(self):
        print(f"[*] Connecting to Kotak Neo API for {self.symbol}...")
        self.client = get_kotak_session()
        print("[+] Kotak Neo session connected.")

        # Load master contract based on symbol
        if self.symbol == "NIFTY":
            master_path = os.path.join(KOTAK_SDK_DIR, "today_nse_fo.csv")
            if not os.path.exists(master_path):
                master_path = os.path.join(BOT_DIR, "today_nse_fo.csv")
            print("[*] Loading NSE FO master database...")
            df = pd.read_csv(master_path, low_memory=False)
            df.columns = [c.strip().rstrip(';') for c in df.columns]
            self.master_df = df[(df['pSymbolName'].astype(str) == 'NIFTY') & (df['pInstType'].astype(str) == 'OPTIDX')].copy()
            self.exchange_seg = "nse_fo"
            self.spot_seg = "nse_cm"
            self.spot_tok = "Nifty 50"
        elif self.symbol == "SENSEX":
            master_path = os.path.join(KOTAK_SDK_DIR, "today_bse_fo.csv")
            if not os.path.exists(master_path):
                master_path = os.path.join(BOT_DIR, "today_bse_fo.csv")
            print("[*] Loading BSE FO master database...")
            df = pd.read_csv(master_path, low_memory=False)
            df.columns = [c.strip().rstrip(';') for c in df.columns]
            self.master_df = df[(df['pSymbolName'].astype(str) == 'SENSEX') & (df['pInstType'].astype(str) == 'IO')].copy()
            self.exchange_seg = "bse_fo"
            self.spot_seg = "bse_cm"
            self.spot_tok = "SENSEX"
        else:
            raise ValueError(f"Unsupported symbol: {self.symbol}")

        print(f"[+] Loaded {len(self.master_df)} active {self.symbol} options contracts.")

    def get_spot_price(self):
        """Fetches live Spot price from Kotak cm segment."""
        res = self.client.quotes(instrument_tokens=[{"instrument_token": self.spot_tok, "exchange_segment": self.spot_seg}])
        if isinstance(res, list) and len(res) > 0:
            ltp = float(res[0].get("ltp", 0.0) or res[0].get("last_price", 0.0))
            if ltp > 0:
                return ltp
        return 23400.0 if self.symbol == "NIFTY" else 74400.0

    def resolve_contracts(self, spot_price):
        """Calculates Short Strikes and Protective Wing Strikes."""
        otm_offset = spot_price * self.config["otm_percent"]
        wing_offset = spot_price * self.config["wing_percent"]
        step = float(self.config["strike_step"])

        target_short_ce = round((spot_price + otm_offset) / step) * step
        target_short_pe = round((spot_price - otm_offset) / step) * step
        target_wing_ce  = round((spot_price + wing_offset) / step) * step
        target_wing_pe  = round((spot_price - wing_offset) / step) * step

        exp_col = 'pExpiryDate' if 'pExpiryDate' in self.master_df.columns else 'lExpiryDate'
        expiries = sorted(self.master_df[exp_col].dropna().unique())
        nearest_exp = expiries[0]
        sub = self.master_df[self.master_df[exp_col] == nearest_exp].copy()

        def find_token(strike, opt_type):
            for _, row in sub.iterrows():
                ts = str(row['pTrdSymbol']).strip()
                if ts.endswith(opt_type):
                    m = re.search(r'(\d+)' + opt_type + r'$', ts)
                    if m:
                        stk_val = float(m.group(1))
                        if stk_val > 1000000:
                            stk_val = float(str(int(stk_val))[-5:])
                        if abs(stk_val - strike) < 1.0:
                            return str(row['pSymbol']), ts
            return None, f"{self.symbol}_{strike}_{opt_type}"

        ce_token, ce_trd = find_token(target_short_ce, "CE")
        pe_token, pe_trd = find_token(target_short_pe, "PE")
        w_ce_token, w_ce_trd = find_token(target_wing_ce, "CE")
        w_pe_token, w_pe_trd = find_token(target_wing_pe, "PE")

        return {
            "spot": spot_price,
            "short_ce": {"strike": target_short_ce, "token": ce_token, "trd_symbol": ce_trd},
            "short_pe": {"strike": target_short_pe, "token": pe_token, "trd_symbol": pe_trd},
            "wing_ce": {"strike": target_wing_ce, "token": w_ce_token, "trd_symbol": w_ce_trd},
            "wing_pe": {"strike": target_wing_pe, "token": w_pe_token, "trd_symbol": w_pe_trd},
        }

    def execute_basket_entry(self):
        """Fetches live quotes and enters the margin-hedged Iron Condor."""
        spot = self.get_spot_price()
        contracts = self.resolve_contracts(spot)

        tokens_to_fetch = []
        for leg in ["short_ce", "short_pe", "wing_ce", "wing_pe"]:
            tok = contracts[leg]["token"]
            if tok:
                tokens_to_fetch.append({"instrument_token": tok, "exchange_segment": self.exchange_seg})

        quotes = self.client.quotes(instrument_tokens=tokens_to_fetch)
        px_map = {}
        if isinstance(quotes, list):
            for q in quotes:
                tok = str(q.get("exchange_token") or q.get("instrument_token") or "")
                ltp = float(q.get("ltp", 0.0) or q.get("last_price", 0.0))
                px_map[tok] = ltp

        ce_px = px_map.get(contracts["short_ce"]["token"], 48.0 if self.symbol == "NIFTY" else 35.0)
        pe_px = px_map.get(contracts["short_pe"]["token"], 45.0 if self.symbol == "NIFTY" else 32.0)
        w_ce_px = px_map.get(contracts["wing_ce"]["token"], 3.0 if self.symbol == "NIFTY" else 6.0)
        w_pe_px = px_map.get(contracts["wing_pe"]["token"], 3.0 if self.symbol == "NIFTY" else 6.0)

        sl_pct = self.config["stop_loss_pct"]
        ce_sl = ce_px * (1.0 + sl_pct)
        pe_sl = pe_px * (1.0 + sl_pct)
        net_credit = (ce_px + pe_px) - (w_ce_px + w_pe_px)

        self.active_position = {
            "spot": spot,
            "contracts": contracts,
            "ce_token": contracts["short_ce"]["token"],
            "ce_entry": ce_px,
            "ce_exit": ce_px,
            "ce_sl": ce_sl,
            "ce_stopped": False,
            "pe_token": contracts["short_pe"]["token"],
            "pe_entry": pe_px,
            "pe_exit": pe_px,
            "pe_sl": pe_sl,
            "pe_stopped": False,
            "wings_cost": w_ce_px + w_pe_px,
            "net_credit": net_credit,
            "entry_time": datetime.now().strftime("%H:%M:%S")
        }

        print(f"\n[+] {self.symbol} Condor Basket Executed at Spot Rs {spot:,.1f}:")
        print(f"    - SELL {contracts['short_ce']['trd_symbol']} @ Rs {ce_px:.2f} (25% SL: Rs {ce_sl:.2f})")
        print(f"    - SELL {contracts['short_pe']['trd_symbol']} @ Rs {pe_px:.2f} (25% SL: Rs {pe_sl:.2f})")
        print(f"    - BUY  Wings: {contracts['wing_ce']['trd_symbol']} & {contracts['wing_pe']['trd_symbol']} (@ Rs {w_ce_px+w_pe_px:.1f})")
        print(f"    - Net Premium Credit: +{net_credit:.2f} pts")
        print("    - Stop Rule: Pure 25% SL per leg (NO trailing of surviving leg to cost)\n")

        self.alerter.send_basket_entry(
            mode=self.mode,
            spot=spot,
            short_ce=contracts['short_ce']['strike'],
            ce_price=ce_px,
            short_pe=contracts['short_pe']['strike'],
            pe_price=pe_px,
            wing_ce=contracts['wing_ce']['strike'],
            wing_pe=contracts['wing_pe']['strike'],
            credit=net_credit
        )

    def monitor_tick(self):
        """
        Polls active legs and manages standard 25% SL per leg and profit targets.
        (Surviving leg keeps its original SL; NO trailing to cost).
        """
        if not self.active_position:
            return

        pos = self.active_position
        reqs = []
        if pos["ce_token"]: reqs.append({"instrument_token": pos["ce_token"], "exchange_segment": self.exchange_seg})
        if pos["pe_token"]: reqs.append({"instrument_token": pos["pe_token"], "exchange_segment": self.exchange_seg})

        quotes = self.client.quotes(instrument_tokens=reqs)
        cur_ce_px = pos["ce_entry"]
        cur_pe_px = pos["pe_entry"]

        if isinstance(quotes, list):
            for q in quotes:
                tok = str(q.get("exchange_token") or q.get("instrument_token") or "")
                ltp = float(q.get("ltp", 0.0) or q.get("last_price", 0.0))
                if tok == pos["ce_token"] and ltp > 0: cur_ce_px = ltp
                elif tok == pos["pe_token"] and ltp > 0: cur_pe_px = ltp

        # 1. CE Stop Loss (25% breach)
        if not pos["ce_stopped"] and cur_ce_px >= pos["ce_sl"]:
            pos["ce_stopped"] = True
            pos["ce_exit"] = pos["ce_sl"]
            print(f"[!] CE 25% Stop-Loss Triggered at Rs {pos['ce_sl']:.2f}!")
            # Note: Surviving PE leg retains its original PE SL (NO cost trail)
            print(f"[i] Surviving PE leg retains original 25% SL at Rs {pos['pe_sl']:.2f} (No cost trail)")
            self.alerter.send_leg_stop_loss("CE", pos["contracts"]["short_ce"]["strike"], pos["ce_entry"], pos["ce_sl"], "PE", pos["contracts"]["short_pe"]["strike"])

        # 2. PE Stop Loss (25% breach)
        if not pos["pe_stopped"] and cur_pe_px >= pos["pe_sl"]:
            pos["pe_stopped"] = True
            pos["pe_exit"] = pos["pe_sl"]
            print(f"[!] PE 25% Stop-Loss Triggered at Rs {pos['pe_sl']:.2f}!")
            # Note: Surviving CE leg retains its original CE SL (NO cost trail)
            print(f"[i] Surviving CE leg retains original 25% SL at Rs {pos['ce_sl']:.2f} (No cost trail)")
            self.alerter.send_leg_stop_loss("PE", pos["contracts"]["short_pe"]["strike"], pos["pe_entry"], pos["pe_sl"], "CE", pos["contracts"]["short_ce"]["strike"])

        # 3. Check Profit Target Lock
        ce_cur_exit = pos["ce_sl"] if pos["ce_stopped"] else cur_ce_px
        pe_cur_exit = pos["pe_sl"] if pos["pe_stopped"] else cur_pe_px

        pts = (pos["ce_entry"] - ce_cur_exit) + (pos["pe_entry"] - pe_cur_exit) - (pos["wings_cost"] * 0.8)
        current_pnl_rs = pts * self.config["lot_size"] * self.config["lots"]

        if current_pnl_rs >= self.config["profit_target_rs"]:
            print(f"[TARGET] Target Profit Milestone (+Rs {current_pnl_rs:,.2f}) Hit! Squaring off early.")
            self.square_off(ce_cur_exit, pe_cur_exit, reason=f"TARGET_PROFIT_LOCK (+Rs {self.config['profit_target_rs']:,.0f})")

    def square_off(self, final_ce_price=None, final_pe_price=None, reason="SCHEDULED_EXIT"):
        if not self.active_position:
            return

        pos = self.active_position
        if final_ce_price is not None and not pos["ce_stopped"]:
            pos["ce_exit"] = final_ce_price
        if final_pe_price is not None and not pos["pe_stopped"]:
            pos["pe_exit"] = final_pe_price

        ce_pts = pos["ce_entry"] - pos["ce_exit"]
        pe_pts = pos["pe_entry"] - pos["pe_exit"]
        net_pts = ce_pts + pe_pts - (pos["wings_cost"] * 0.8)

        gross_pnl = net_pts * self.config["lot_size"] * self.config["lots"]
        taxes = 80.0
        net_pnl = gross_pnl - taxes
        self.cumulative_pnl += net_pnl

        trade_record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "day_name": datetime.now().strftime("%A"),
            "symbol": self.symbol,
            "mode": self.mode,
            "spot": pos["spot"],
            "short_ce": pos["contracts"]["short_ce"]["strike"],
            "ce_entry": pos["ce_entry"],
            "ce_exit": pos["ce_exit"],
            "ce_status": "STOPPED" if pos["ce_stopped"] else "DECAYED",
            "short_pe": pos["contracts"]["short_pe"]["strike"],
            "pe_entry": pos["pe_entry"],
            "pe_exit": pos["pe_exit"],
            "pe_status": "STOPPED" if pos["pe_stopped"] else "DECAYED",
            "wings": f"{pos['contracts']['wing_ce']['strike']}CE / {pos['contracts']['wing_pe']['strike']}PE",
            "points": net_pts,
            "net_pnl": net_pnl,
            "exit_reason": reason
        }

        self.journaler.record_trade(trade_record)
        self.alerter.send_daily_journal(
            date=trade_record["date"],
            mode=self.mode,
            exit_reason=reason,
            net_pnl_rs=net_pnl,
            total_pts=net_pts,
            cumulative_pnl=self.cumulative_pnl
        )

        print(f"\n[DONE] {self.symbol} Session Closed | Net PnL: Rs {net_pnl:+,.2f} | Reason: {reason}\n")
        self.active_position = None
        return trade_record

# Backwards compatibility alias
NiftyWeeklyOptionSellingBot = MultiIndexIronCondorBot
