import os
import json
import threading
import requests

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "telegram_config.json")
# Fallback to crude_oil_trading if local not present
SHARED_CONFIG_PATH = r"C:\Users\Ridham\.gemini\antigravity-ide\scratch\crude_oil_trading\engine\telegram_config.json"

class TelegramAlerter:
    def __init__(self):
        self.bot_token = None
        self.chat_id = None
        self.enabled = False
        self.load_config()

    def load_config(self):
        # 1. Environment variables (GitHub Actions Cloud mode)
        env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        env_chat = os.environ.get("TELEGRAM_CHAT_ID")
        if env_token and env_chat:
            self.bot_token = env_token.strip()
            self.chat_id = str(env_chat).strip()
            self.enabled = True
            print("[+] Telegram Alerter Connected via Environment Variables.")
            return

        # 2. Local config fallback
        target = CONFIG_PATH if os.path.exists(CONFIG_PATH) else SHARED_CONFIG_PATH
        if os.path.exists(target):
            try:
                with open(target, "r") as f:
                    cfg = json.load(f)
                    self.bot_token = cfg.get("telegram_bot_token") or cfg.get("bot_token", "")
                    self.chat_id = str(cfg.get("telegram_chat_id") or cfg.get("chat_id", ""))
                    if self.bot_token and self.chat_id:
                        self.enabled = True
                        print("[+] Telegram Alerter Connected.")
            except Exception as e:
                print(f"[!] Telegram config error: {e}")

    def _send(self, text):
        if not self.enabled:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[!] Telegram dispatch failed: {e}")

    def notify(self, text):
        """Asynchronous non-blocking message dispatch"""
        if self.enabled:
            threading.Thread(target=self._send, args=(text,), daemon=True).start()

    def send_bot_startup(self, mode, symbol, lots, capital):
        msg = (
            f"🟢 <b>[OPTION SELLING BOT] LIVE & READY</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Index:</b> {symbol}\n"
            f"💼 <b>Mode:</b> {mode} (Paper/Live)\n"
            f"📊 <b>Position Size:</b> {lots} Lot\n"
            f"⏰ <b>Entry Time:</b> 09:25 AM IST\n"
            f"🏁 <b>Exit Time:</b> 01:30 PM IST (Theta Target)\n"
            f"🎯 <b>Rules:</b> Independent 25% Stop-Loss per leg (No cost trail)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <i>Waiting for 09:25 AM market entry...</i>"
        )
        self.notify(msg)

    def send_basket_entry(self, mode, spot, short_ce, ce_price, short_pe, pe_price, wing_ce, wing_pe, credit):
        msg = (
            f"⚡ <b>[OPTION SELLING BOT] NEW TRADE ENTERED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>Current Spot:</b> ₹{spot:,.1f}\n\n"
            f"📉 <b>SELL CALL (CE):</b> {short_ce} CE\n"
            f"   • Premium Sold: ₹{ce_price:.2f}\n"
            f"   • Stop-Loss (25%): ₹{ce_price*1.25:.2f}\n\n"
            f"📉 <b>SELL PUT (PE):</b> {short_pe} PE\n"
            f"   • Premium Sold: ₹{pe_price:.2f}\n"
            f"   • Stop-Loss (25%): ₹{pe_price*1.25:.2f}\n\n"
            f"🛡️ <b>Hedge Wings (Margin Protection):</b>\n"
            f"   • Buy {wing_ce} CE & {wing_pe} PE\n\n"
            f"💰 <b>Total Net Credit Received:</b> +{credit:.2f} points\n"
            f"🎯 <b>Target Profit:</b> ₹3,000 | <b>Time Exit:</b> 01:30 PM\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <i>Monitoring ticks for Stop-Loss or Target.</i>"
        )
        self.notify(msg)

    def send_leg_stop_loss(self, stopped_leg, strike, entry_px, exit_px, surviving_leg, surviving_stk):
        loss_pts = exit_px - entry_px
        msg = (
            f"⚠️ <b>[OPTION SELLING BOT] STOP-LOSS HIT ({stopped_leg})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔴 <b>Stopped Leg:</b> {strike} {stopped_leg}\n"
            f"   • Sold at: ₹{entry_px:.2f}\n"
            f"   • Exited at (25% SL): ₹{exit_px:.2f}\n"
            f"   • Points Cut: -{loss_pts:.2f} pts\n\n"
            f"🟢 <b>Surviving Leg:</b> {surviving_stk} {surviving_leg}\n"
            f"   • Status: <b>Keeps original 25% SL</b> (Trailing to cost is disabled)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ <i>Surviving leg continues monitoring until 01:30 PM.</i>"
        )
        self.notify(msg)

    def send_daily_journal(self, date, mode, exit_reason, net_pnl_rs, total_pts, cumulative_pnl):
        status_icon = "🎉 <b>PROFITABLE SESSION</b>" if net_pnl_rs >= 0 else "🛑 <b>LOSS SESSION</b>"
        pnl_symbol = "+" if net_pnl_rs >= 0 else ""
        msg = (
            f"📊 <b>[OPTION SELLING BOT] SESSION COMPLETE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Date:</b> {date}\n"
            f"🔔 <b>Outcome:</b> {status_icon}\n"
            f"🚪 <b>Exit Reason:</b> {exit_reason}\n"
            f"📈 <b>Points Captured:</b> {total_pts:+.2f} pts\n"
            f"💵 <b>Today's Net P&L:</b> <b>{pnl_symbol}₹{net_pnl_rs:,.2f}</b>\n"
            f"💼 <b>Total Cumulative P&L:</b> ₹{cumulative_pnl:,.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 <i>Ledger recorded to GitHub. Bot now sleeping until tomorrow.</i>"
        )
        self.notify(msg)
