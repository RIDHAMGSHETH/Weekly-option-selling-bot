#!/usr/bin/env bash
# ==============================================================================
# Interactive Live Terminal Monitor for Linux Mint (NIFTY & BSE SENSEX)
# ==============================================================================

# Ensure script runs from its directory
cd "$(dirname "$0")"

# Use venv python if available, otherwise fallback to system python3
if [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="./venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

while true; do
    clear
    echo "==============================================================================="
    echo "       ⚡ 0-DTE HYBRID MASTER REAL-TIME QUANT TRADING SOFTWARE (LINUX) ⚡"
    echo "       NIFTY 50 (Tuesdays) & BSE SENSEX (Thursdays) Live Monitoring Engine"
    echo "==============================================================================="
    echo ""
    echo "   [1] Launch NIFTY 50 Live 0-DTE Real-Time Monitor (Tuesdays)"
    echo "   [2] Launch BSE SENSEX Live 0-DTE Real-Time Monitor (Thursdays)"
    echo "   [3] Exit Monitor"
    echo ""
    echo "==============================================================================="
    read -p "Select an option (1-3): " choice

    case $choice in
        1)
            clear
            echo "Starting NIFTY 50 0-DTE Live Stream Monitor..."
            echo ""
            $PYTHON_CMD live_hybrid_master_terminal.py NIFTY
            read -p "Press Enter to return to menu..."
            ;;
        2)
            clear
            echo "Starting BSE SENSEX 0-DTE Live Stream Monitor..."
            echo ""
            $PYTHON_CMD live_hybrid_master_terminal.py SENSEX
            read -p "Press Enter to return to menu..."
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid selection. Please choose 1, 2, or 3."
            sleep 2
            ;;
    esac
done
