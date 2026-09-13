@echo off
title NIFTY 0-DTE QUANT TRADING BOT
color 0A
cd /d "C:\Users\Ridham\.gemini\antigravity-ide\scratch\nifty_0dte_bot"

echo ===============================================================================
echo            NIFTY 0-DTE INSTITUTIONAL QUANT TRADING BOT
echo ===============================================================================
echo [i] Python Environment: Active
echo [i] Strategy: Dynamic 0-DTE Iron Condor with 25%% SL Guard
echo [i] Journaling: Enabled (CSV + GitHub Markdown)
echo [i] Telegram: Connected to @AntigravityPcControlBot
echo ===============================================================================

python nifty_0dte_bot.py
pause
