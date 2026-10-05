#!/usr/bin/env bash
# ==============================================================================
# Autonomous Background Scheduler Runner for Linux Mint
# ==============================================================================

cd "$(dirname "$0")"

if [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="./venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

echo "=============================================================================="
echo " Starting Autonomous 0-DTE Option Selling Scheduler on Linux..."
echo " Target: NIFTY (Tuesdays) & BSE SENSEX (Thursdays)"
echo " Logs will be streamed live. Press Ctrl+C to terminate."
echo "=============================================================================="

$PYTHON_CMD automated_option_selling_scheduler.py
