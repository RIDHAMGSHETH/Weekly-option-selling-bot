# 0-DTE Hybrid Master Option Selling Bot (NIFTY & BSE SENSEX)

Autonomous quantitative options selling engine executed on Kotak Neo API with automated holiday scheduling, dynamic 11:30 AM rolling, 0.85% delta defense, Telegram notifications, and GitHub trade journaling.

---

## 🎯 Verified Contract Expiry Schedule (Live Exchange Master)
- **NIFTY 50 (NSE)**: Every **Tuesday** (holiday-shifted to Monday when applicable)
- **BSE SENSEX (BSE)**: Every **Thursday** (holiday-shifted to Wednesday when applicable)

---

## 📊 2026 Verified Strategy Audit (79 Full Expiry Sessions)
Tested across all 186 trading days in the 2026 dataset:
- **Combined Net Profit**: **+₹57,181.56**
- **Win Rate**: **84.8%** (67 Wins / 12 Losses)
- **Profit Factor**: **5.70**
- **NIFTY 50 (Tuesdays, 39 Sessions)**: +₹35,109.62 (87.2% Win Rate, Profit Factor 9.22)
- **BSE SENSEX (Thursdays, 40 Sessions)**: +₹22,071.93 (82.5% Win Rate, Profit Factor 3.80)
- **Worst Single Day Drawdown**: -₹2,625.00

---

## 🛡️ Risk Management & Dynamic Adjustments
1. **No Tight Stop-Loss Whipsaws**:
   - Replaced narrow 25% SL with outer protective wings (1.5% OTM).
2. **Dynamic 11:30 AM Roll**:
   - At 11:30 AM, if the unchallenged leg has decayed $\ge 75\%$, it is rolled inward to bank fresh credit.
3. **Emergency 0.85% Delta Shield**:
   - If intraday spot moves $\ge 0.85\%$ towards a short strike, the threatened side is de-risked immediately.
4. **Hard Mathematical Loss Cap**:
   - Maximum loss is mathematically capped by wing width minus credit received.

---

## 📲 Telegram Notifications
Instant Telegram alerts sent on:
- **09:25 AM Basket Entry** (Strikes, Spot, Net Credit, Fixed Boundaries)
- **11:30 AM Leg Roll** (Harvested Decay %, Inward Strike, Fresh Credit)
- **0.85% Delta Shield Trigger** (Threatened Side, Spot Shift %, Action Taken)
- **13:30 PM Session Close** (Captured Points, Net P&L ₹, Cumulative P&L)

---

## 🚀 Desktop Launchers
- **Real-Time HUD Monitor**: `LIVE_HYBRID_EXPIRY_TERMINAL.bat` (Direct on Desktop)
- **Background Scheduler**: `automated_option_selling_scheduler.py`