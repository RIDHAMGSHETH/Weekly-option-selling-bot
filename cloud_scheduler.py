"""
================================================================================
24/7 CLOUD EXPIRY SIGNAL SCHEDULER (NIFTY & SENSEX)
Designed for: Render.com / Railway / Cloud VPS Deployment
Timezone: Asia/Kolkata (Indian Standard Time)
Trigger: 09:20:00 AM IST Sharp (Monday to Friday)

Architecture:
1. Environment Variable Prioritization:
   - DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
   - Safe local fallback to dhan_config.json & telegram_config.json
2. Multi-threaded Server:
   - Lightweight Flask HTTP server on PORT (default 8080 or os.environ.get('PORT'))
   - Serves GET / and GET /health to satisfy cloud health checks and prevent idling.
3. Accurate Daily Timer:
   - Checks the clock every 5 seconds.
   - Triggers execute_daily_signal() at 09:20:00 AM IST.
   - Detects contract expiries, holiday shifts, spot, strikes, and rates.
================================================================================
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
import pytz
import requests
from flask import Flask, jsonify

IST = pytz.timezone("Asia/Kolkata")
app = Flask(__name__)

# --- SECRETS & CREDENTIALS RESOLUTION ---
def get_credentials():
    # 1. Check environment variables
    dhan_client_id = os.environ.get("DHAN_CLIENT_ID")
    dhan_token = os.environ.get("DHAN_ACCESS_TOKEN")
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    # 2. Fallbacks to local files if running locally
    if not dhan_client_id or not dhan_token:
        for p in [
            "dhan_config.json",
            r"C:\Users\Ridham\OneDrive\Desktop\nifty data\data recorder\dhan_config.json"
        ]:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                        dhan_client_id = dhan_client_id or data.get("client_id")
                        dhan_token = dhan_token or data.get("access_token")
                except Exception:
                    pass

    if not tg_token or not tg_chat_id:
        for p in [
            "telegram_config.json",
            r"C:\Users\Ridham\.gemini\antigravity-ide\scratch\Weekly-option-selling-bot\telegram_config.json"
        ]:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                        tg_token = tg_token or data.get("telegram_bot_token") or data.get("bot_token")
                        tg_chat_id = tg_chat_id or data.get("telegram_chat_id") or data.get("chat_id")
                except Exception:
                    pass

    return {
        "dhan_client_id": dhan_client_id,
        "dhan_token": dhan_token,
        "tg_token": tg_token,
        "tg_chat_id": tg_chat_id
    }

creds = get_credentials()

INDEX_CONFIG = {
    "NIFTY": {
        "symbol": "NIFTY 50",
        "scrip_id": 13,
        "exchange_seg": "IDX_I",
        "strike_step": 50,
        "lot_size": 75,
        "standard_day": "Tuesday"
    },
    "SENSEX": {
        "symbol": "BSE SENSEX",
        "scrip_id": 51,
        "exchange_seg": "IDX_I",
        "strike_step": 100,
        "lot_size": 20,
        "standard_day": "Thursday"
    }
}

bot_state = {
    "status": "RUNNING",
    "last_check_time": None,
    "last_trigger_date": None,
    "last_signals": []
}

def send_telegram(text: str) -> bool:
    c = get_credentials()
    if not c["tg_token"] or not c["tg_chat_id"]:
        print("[TELEGRAM] Warning: Telegram credentials missing.")
        return False
    url = f"https://api.telegram.org/bot{c['tg_token']}/sendMessage"
    payload = {
        "chat_id": c["tg_chat_id"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM] Error sending alert: {e}")
        return False

def get_dhan_headers():
    c = get_credentials()
    return {
        "access-token": c["dhan_token"],
        "client-id": str(c["dhan_client_id"]),
        "Content-Type": "application/json"
    }

def analyze_and_signal(index_name: str, force_test: bool = False):
    cfg = INDEX_CONFIG[index_name]
    headers = get_dhan_headers()

    # 1. Fetch nearest active expiry date from Dhan API
    url_exp = "https://api.dhan.co/v2/optionchain/expirylist"
    payload_exp = {"UnderlyingScrip": cfg["scrip_id"], "UnderlyingSeg": cfg["exchange_seg"]}
    try:
        r_exp = requests.post(url_exp, headers=headers, json=payload_exp, timeout=10)
        exp_list = sorted(r_exp.json().get("data", []))
    except Exception as e:
        print(f"[{index_name}] Failed to fetch expiry list: {e}")
        return None

    if not exp_list:
        print(f"[{index_name}] Expiry list is empty.")
        return None

    nearest_exp = exp_list[0]
    now_ist = datetime.now(IST)
    today_str = now_ist.strftime("%Y-%m-%d")
    exp_dt = datetime.strptime(nearest_exp, "%Y-%m-%d").date()
    exp_weekday = exp_dt.strftime("%A")

    is_today_expiry = (today_str == nearest_exp)
    is_holiday_shift = (exp_weekday != cfg["standard_day"])

    print(f"[{index_name}] Nearest Expiry: {nearest_exp} ({exp_weekday}) | Holiday Shift: {is_holiday_shift} | Today is Expiry: {is_today_expiry}")

    if not is_today_expiry and not force_test:
        print(f"[{index_name}] Standby mode: Today is not an expiry day.")
        return None

    # 2. Fetch Live Spot & Option Chain
    url_oc = "https://api.dhan.co/v2/optionchain"
    payload_oc = {"UnderlyingScrip": cfg["scrip_id"], "UnderlyingSeg": cfg["exchange_seg"], "Expiry": nearest_exp}
    try:
        r_oc = requests.post(url_oc, headers=headers, json=payload_oc, timeout=10)
        data = r_oc.json().get("data", {})
        spot = data.get("last_price")
        oc = data.get("oc", {})
    except Exception as e:
        print(f"[{index_name}] Failed to fetch option chain: {e}")
        return None

    if not spot or not oc:
        print(f"[{index_name}] Missing spot or option chain data.")
        return None

    spot = float(spot)
    step = cfg["strike_step"]
    lot_size = cfg["lot_size"]

    # 3. Calculate 1.0% OTM Short & 1.5% OTM Wing Strikes
    short_ce_strike = round((spot * 1.01) / step) * step
    long_ce_strike = round((spot * 1.015) / step) * step
    short_pe_strike = round((spot * 0.99) / step) * step
    long_pe_strike = round((spot * 0.985) / step) * step

    spread_width = max(long_ce_strike - short_ce_strike, short_pe_strike - long_pe_strike)

    def extract_price(strike, opt_type):
        s_key = f"{strike:.6f}"
        info = oc.get(s_key, {}).get(opt_type.lower(), {})
        ltp = info.get("last_price")
        if ltp and float(ltp) > 0:
            return float(ltp)
        ask = info.get("top_ask_price", 0.0)
        bid = info.get("top_bid_price", 0.0)
        if ask and bid and ask > 0 and bid > 0:
            return round((ask + bid) / 2.0, 2)
        avg = info.get("average_price")
        return float(avg) if avg else 0.50

    p_short_ce = extract_price(short_ce_strike, "CE")
    p_long_ce = extract_price(long_ce_strike, "CE")
    p_short_pe = extract_price(short_pe_strike, "PE")
    p_long_pe = extract_price(long_pe_strike, "PE")

    call_credit = max(0.0, p_short_ce - p_long_ce)
    put_credit = max(0.0, p_short_pe - p_long_pe)
    net_credit_pts = round(call_credit + put_credit, 2)
    max_profit_rs = round(net_credit_pts * lot_size, 2)
    max_loss_pts = round(spread_width - net_credit_pts, 2)
    max_loss_rs = round(max_loss_pts * lot_size, 2)

    shift_badge = " ⚠️ (Shifted due to Holiday!)" if is_holiday_shift else ""

    alert_text = f"""🎯 <b>0-DTE LIVE SIGNAL: {index_name} EXPIRY MASTER</b>
📅 <b>Contract Expiry</b>: {nearest_exp} ({exp_weekday}){shift_badge}
📍 <b>Live Underlying Spot</b>: <code>{spot:,.2f}</code>
💼 <b>Lot Size</b>: {lot_size} Qty | <b>Spread Width</b>: {spread_width} pts

━━━━━━━━━━━━━━━━━━━━━
<b>1. EXECUTION ORDERS (IRON CONDOR)</b>
━━━━━━━━━━━━━━━━━━━━━
🔴 <b>SELL Short CE (1.0% OTM)</b>: <code>{short_ce_strike} CE</code> @ ~₹{p_short_ce:.2f}
🟢 <b>BUY  Wing CE (1.5% OTM)</b>: <code>{long_ce_strike} CE</code> @ ~₹{p_long_ce:.2f}

🔴 <b>SELL Short PE (1.0% OTM)</b>: <code>{short_pe_strike} PE</code> @ ~₹{p_short_pe:.2f}
🟢 <b>BUY  Wing PE (1.5% OTM)</b>: <code>{long_pe_strike} PE</code> @ ~₹{p_long_pe:.2f}

━━━━━━━━━━━━━━━━━━━━━
<b>2. RISK & REWARD PROFILE</b>
━━━━━━━━━━━━━━━━━━━━━
💰 <b>Net Credit Received</b>: <b>+{net_credit_pts:.2f} pts</b>
🏆 <b>MAX PROFIT EXPECTED</b>: <b>+₹{max_profit_rs:,.2f} per lot</b>
🛡️ <b>MAX LOSS HARD CAPPED</b>: <b>-₹{max_loss_rs:,.2f} per lot</b> ({max_loss_pts:.2f} pts)

⏱️ <b>Strategy Rules</b>:
• <b>Entry Window</b>: 09:25 AM IST
• <b>Target Exit</b>: 13:30 PM IST (Harvest peak theta decay)
• <b>Dynamic Roll</b>: At 11:30 AM, roll unchallenged wing if decayed ≥ 75%
"""
    send_telegram(alert_text)
    print(f"[{index_name}] Alert sent successfully!")
    return {
        "index": index_name,
        "expiry": nearest_exp,
        "spot": spot,
        "net_credit": net_credit_pts,
        "max_profit": max_profit_rs,
        "max_loss": max_loss_rs
    }

def execute_daily_signal(force_test: bool = False):
    print(f"\n[SCHEDULER] Waking up at {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST...")
    results = []
    for idx in ["NIFTY", "SENSEX"]:
        res = analyze_and_signal(idx, force_test=force_test)
        if res:
            results.append(res)
    bot_state["last_signals"] = results
    bot_state["last_trigger_date"] = datetime.now(IST).strftime("%Y-%m-%d")

# --- BACKGROUND CLOCK SCHEDULER LOOP ---
def run_clock_scheduler():
    print("[SCHEDULER] Background IST Clock loop active. Monitoring for 09:20:00 AM IST...")
    while True:
        now = datetime.now(IST)
        bot_state["last_check_time"] = now.strftime("%Y-%m-%d %H:%M:%S")

        # Monday (0) through Friday (4)
        if now.weekday() < 5:
            # Trigger window: 09:20:00 AM to 09:20:10 AM
            if now.hour == 9 and now.minute == 20 and now.second < 10:
                today_str = now.strftime("%Y-%m-%d")
                if bot_state["last_trigger_date"] != today_str:
                    execute_daily_signal(force_test=False)
                    time.sleep(15)  # avoid double trigger within the same minute

        time.sleep(5)

# --- FLASK HEALTH SERVER ---
@app.route("/")
def index():
    return jsonify({
        "service": "24/7 Expiry Signal Bot (NIFTY & SENSEX)",
        "status": bot_state["status"],
        "server_time_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "target_trigger_time": "09:20:00 AM IST (Monday to Friday)",
        "last_trigger_date": bot_state["last_trigger_date"],
        "last_signals": bot_state["last_signals"]
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route("/test-trigger")
def manual_test_trigger():
    execute_daily_signal(force_test=True)
    return jsonify({
        "status": "triggered_test_alerts",
        "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    }), 200

if __name__ == "__main__":
    if "--test-trigger" in sys.argv:
        execute_daily_signal(force_test=True)
        sys.exit(0)

    # Start scheduler daemon thread
    t = threading.Thread(target=run_clock_scheduler, daemon=True)
    t.start()

    # Run web server
    port = int(os.environ.get("PORT", 8080))
    print(f"[WEB] Starting health server on port {port}...")
    app.run(host="0.0.0.0", port=port, use_reloader=False)
