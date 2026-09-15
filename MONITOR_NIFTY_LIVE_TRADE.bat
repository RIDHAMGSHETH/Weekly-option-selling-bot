@echo off
title LIVE NIFTY OPTION SELLING RADAR & TRADE MONITOR
cd /d "C:\Users\Ridham\.gemini\antigravity-ide\scratch\Weekly-option-selling-bot"
color 0B

echo ===============================================================================
echo        ⚡ LIVE NIFTY OPTION SELLING EXECUTION & PnL MONITOR ⚡
echo ===============================================================================
echo [i] Connecting to Kotak Neo live feed...
echo [i] Displaying real-time premiums, stop loss levels, and tick-by-tick PnL
echo ===============================================================================
echo.

python live_trade_monitor.py

echo.
echo [!] Monitor exited.
pause
