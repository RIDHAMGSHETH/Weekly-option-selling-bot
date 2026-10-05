#!/usr/bin/env bash
# ==============================================================================
# Linux Mint / Ubuntu One-Click Setup & Installer for 0-DTE Hybrid Master Bot
# ==============================================================================

set -e

echo "=============================================================================="
echo "  ⚡ Setting up 0-DTE Hybrid Master Quant Bot on Linux Mint / Ubuntu"
echo "=============================================================================="

# 1. Update package lists and install Python3 & pip
echo "[1/4] Checking system packages (python3, python3-pip, python3-venv, git)..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git curl

# 2. Setup Virtual Environment
echo "[2/4] Creating Python virtual environment (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 3. Install requirements
echo "[3/4] Installing required Python dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Check Configs
echo "[4/4] Checking local configuration files..."
if [ ! -f "kotak_config.json" ]; then
    if [ -f "kotak_config.json.example" ]; then
        cp kotak_config.json.example kotak_config.json
        echo "[!] Created kotak_config.json from template. Please update your Kotak API credentials."
    fi
fi

if [ ! -f "telegram_config.json" ]; then
    echo '{"telegram_bot_token": "", "telegram_chat_id": ""}' > telegram_config.json
    echo "[!] Created telegram_config.json. Please add your Telegram Bot Token and Chat ID if needed."
fi

chmod +x run_monitor.sh run_scheduler.sh 2>/dev/null || true

echo "=============================================================================="
echo "  ✅ Setup Complete! You can now start the software:"
echo "     • Live Terminal Monitor : ./run_monitor.sh"
echo "     • Background Scheduler  : ./run_scheduler.sh"
echo "=============================================================================="
