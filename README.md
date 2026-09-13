# Weekly Option Selling Bot (Nifty 0-DTE & Weekly Iron Condor)

Autonomous quantitative options selling engine executed on Kotak Neo API with automated holiday scheduling, Telegram notifications, and GitHub trade journaling.

## Strategy Architecture
- **Underlying**: NIFTY 50 Index Options
- **Leg Structure**:
  - **Short Strangle**: $\pm 0.6\%$ OTM Strikes (Short CE + Short PE)
  - **Protective Wings**: $\pm 1.0\%$ OTM Strikes (Long CE + Long PE to unlock 60% margin benefit)
- **Execution Window**:
  - Entry: Exactly at **09:25 AM IST**
  - Exit: **13:30 PM IST** (capturing peak morning theta decay) or earlier on target
- **Risk Management**:
  - **25% Stop-Loss** per leg
  - **Trailing Cost Lock**: If one leg hits SL, the surviving profitable leg trails to entry cost (guaranteeing zero further risk)
  - **Milestone Target Lock**: $+₹3,000$ per lot early exit

---

## Autonomous Holiday & Session Scheduler
Integrated with the official **2026 National Stock Exchange (NSE) Holiday Master**:
- **Weekdays Only**: Automatically sleeps on Saturdays and Sundays.
- **Holiday Filter**: Skips all 20 official NSE market holidays (e.g., Ganesh Chaturthi, Diwali, Good Friday, Holi, Republic Day).
- **Auto-Sync to GitHub**: Automatically commits and pushes the [`logs/TRADING_JOURNAL.md`](file:///C:/Users/Ridham/.gemini/antigravity-ide/scratch/Weekly-option-selling-bot/logs/TRADING_JOURNAL.md) and trade ledger CSV to GitHub upon daily square-off.

---

## 1-Click Launchers
- **Start Autonomous Scheduler**: `START_OPTION_SELLING_SCHEDULER.bat`
- **Manual Verification Runner**: `RUN_NIFTY_0DTE_BOT.bat`