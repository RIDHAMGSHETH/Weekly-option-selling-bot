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
            f"🤖 <b>NIFTY 0-DTE QUANT BOT ONLINE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Status:</b> Active & Monitoring\n"
            f"• <b>Mode:</b> <code>{mode}</code>\n"
            f"• <b>Asset:</b> {symbol} (1 Lot = 75 Qty)\n"
            f"• <b>Active Lots:</b> {lots} (Cap: ₹{capital:,.0f})\n"
            f"• <b>Window:</b> 09:25 AM ➔ 13:30 PM\n"
            f"• <b>Protection:</b> Asymmetric 25% SL + Outer Wings\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <i>Awaiting 09:25 AM Expiry Execution Window...</i>"
        )
        self.notify(msg)

    def send_basket_entry(self, mode, spot, short_ce, ce_price, short_pe, pe_price, wing_ce, wing_pe, credit):
        msg = (
            f"⚡ <b>0-DTE BASKET EXECUTED ({mode})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Nifty Spot:</b> <code>₹{spot:,.1f}</code>\n"
            f"• <b>Short CE:</b> {short_ce} CE @ ₹{ce_price:.2f} (SL: ₹{ce_price*1.25:.2f})\n"
            f"• <b>Short PE:</b> {short_pe} PE @ ₹{pe_price:.2f} (SL: ₹{pe_price*1.25:.2f})\n"
            f"• <b>Hedge Wings:</b> {wing_ce} CE & {wing_pe} PE\n"
            f"• <b>Net Premium Collected:</b> <b>+{credit:.2f} pts</b>\n"
            f"• <b>Target Profit:</b> ₹3,000 | <b>Early Exit:</b> 13:30 PM\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ <i>Individual 25% Stop-Loss Orders Armed & Active</i>"
        )
        self.notify(msg)

    def send_leg_stop_loss(self, stopped_leg, strike, entry_px, exit_px, surviving_leg, surviving_stk):
        loss_pts = exit_px - entry_px
        msg = (
            f"🚨 <b>STOP-LOSS TRIGGERED: {stopped_leg}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Leg Cut:</b> {strike} {stopped_leg}\n"
            f"• <b>Entry:</b> ₹{entry_px:.2f} ➔ <b>Exit:</b> ₹{exit_px:.2f} (-{loss_pts:.2f} pts)\n"
            f"• <b>Surviving Leg:</b> {surviving_stk} {surviving_leg}\n"
            f"• <b>Action:</b> ⚖️ <i>Surviving {surviving_leg} retains standard 25% Stop-Loss (No cost trail)</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        self.notify(msg)

    def send_daily_journal(self, date, mode, exit_reason, net_pnl_rs, total_pts, cumulative_pnl):
        status_icon = "🟢" if net_pnl_rs >= 0 else "🔴"
        msg = (
            f"{status_icon} <b>DAILY TRADING JOURNAL | {date}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Execution Mode:</b> <code>{mode}</code>\n"
            f"• <b>Exit Trigger:</b> {exit_reason}\n"
            f"• <b>Session Net Points:</b> {total_pts:+.2f} pts\n"
            f"• <b>Session P&L:</b> <b>{net_pnl_rs:+,.2f} INR</b>\n"
            f"• <b>Cumulative Balance:</b> <b>₹{cumulative_pnl:,.2f}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 <i>Trade details and tick metrics recorded to GitHub Journal & CSV.</i>"
        )
        self.notify(msg)
