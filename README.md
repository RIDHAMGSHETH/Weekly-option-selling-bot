# 0-DTE Hybrid Master Option Selling Bot (NIFTY & BSE SENSEX)

Autonomous quantitative options selling engine executed on Kotak Neo API with automated holiday scheduling, dynamic 11:30 AM rolling, 0.85% delta defense, Telegram notifications, and GitHub trade journaling.

---

## 🎯 Strategy Architecture (Hybrid Master)
- **Indices & Expiries**:
  - **NIFTY 50 (NSE)**: Every Thursday (holiday-shifted to Wednesday when applicable)
  - **BSE SENSEX (BSE)**: Every Friday (holiday-shifted to Thursday when applicable)
- **Leg Construction (09:25 AM IST Entry)**:
  - **Short Strangle**: $\pm 1.0\%$ OTM Strikes (Short CE + Short PE)
  - **Protective Wings**: $\pm 1.5\%$ OTM Strikes (Long CE + Long PE, margin reduction + hard loss limit)
- **Execution & Exits**:
  - **Square-Off Window**: 13:30 PM IST (capturing peak morning theta decay)
  - **Target Milestone**: $+₹3,000$ per lot early exit

---

## 🛡️ Risk Management & Dynamic Adjustments
1. **No Tight Stop-Loss Whipsaws**:
   - Replaced narrow 25% SL (which stopped out on normal intraday retracements) with outer protective wings.
2. **Dynamic 11:30 AM Roll**:
   - At 11:30 AM, if the unchallenged leg has decayed $\ge 75\%$, it is closed and rolled inward to capture fresh credit.
3. **Emergency 0.85% Delta Shield**:
   - If intraday spot moves $\ge 0.85\%$ towards a short strike, the threatened side is de-risked immediately.
4. **Hard Mathematical Loss Cap**:
   - Maximum loss is mathematically capped by wing width minus credit received.

---

## 📲 Telegram Notifications
Instant Telegram alerts sent on:
- **Bot Startup & Connection Status**
- **09:25 AM Basket Entry** (Strikes, Spot, Net Credit, Fixed Boundaries)
- **11:30 AM Leg Roll** (Harvested Decay %, Inward Strike, Fresh Credit)
- **0.85% Delta Shield Trigger** (Threatened Side, Spot Shift %, Action Taken)
- **13:30 PM Session Close** (Captured Points, Net P&L ₹, Cumulative P&L)

Telegram configuration is loaded from [`telegram_config.json`](telegram_config.json) or environment variables:
- `telegram_bot_token`
- `telegram_chat_id`

---

## 🚀 Desktop Launchers
- **Real-Time HUD Monitor**: `C:\Users\Ridham\OneDrive\Desktop\LIVE_HYBRID_EXPIRY_TERMINAL.bat`
- **Background Scheduler**: `automated_option_selling_scheduler.py`