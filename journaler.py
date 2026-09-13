import os
import csv
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
CSV_LOG_PATH = os.path.join(LOGS_DIR, "trading_journal.csv")
MARKDOWN_JOURNAL = os.path.join(LOGS_DIR, "TRADING_JOURNAL.md")

class TradeJournaler:
    def __init__(self):
        os.makedirs(LOGS_DIR, exist_ok=True)
        self.init_csv()
        self.init_markdown()

    def init_csv(self):
        if not os.path.exists(CSV_LOG_PATH):
            with open(CSV_LOG_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Date", "Day", "Mode", "Nifty_Spot", 
                    "Short_CE", "CE_Entry", "CE_Exit", "CE_Status",
                    "Short_PE", "PE_Entry", "PE_Exit", "PE_Status",
                    "Hedge_Wings", "Gross_Points", "Net_PnL_Rs", "Exit_Reason"
                ])

    def init_markdown(self):
        if not os.path.exists(MARKDOWN_JOURNAL):
            with open(MARKDOWN_JOURNAL, "w", encoding="utf-8") as f:
                f.write("# 📓 Quantitative 0-DTE Trade Execution Journal\n\n")
                f.write("Automated GitHub Ledger tracking every live/paper 0-DTE execution, strike selection, and stop-loss event.\n\n")
                f.write("| Date | Day | Mode | Spot | Strikes (CE / PE) | Exit Reason | Net Points | Net P&L (₹) |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: |\n")

    def record_trade(self, trade_data):
        # 1. Append to CSV
        with open(CSV_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                trade_data["date"],
                trade_data["day_name"],
                trade_data["mode"],
                trade_data["spot"],
                trade_data["short_ce"],
                trade_data["ce_entry"],
                trade_data["ce_exit"],
                trade_data["ce_status"],
                trade_data["short_pe"],
                trade_data["pe_entry"],
                trade_data["pe_exit"],
                trade_data["pe_status"],
                trade_data.get("wings", "Yes"),
                round(trade_data["points"], 2),
                round(trade_data["net_pnl"], 2),
                trade_data["exit_reason"]
            ])

        # 2. Append to Markdown Journal
        pnl_str = f"+₹{trade_data['net_pnl']:,.2f}" if trade_data['net_pnl'] >= 0 else f"-₹{abs(trade_data['net_pnl']):,.2f}"
        pts_str = f"{trade_data['points']:+.2f}"
        strikes_str = f"{trade_data['short_ce']} CE / {trade_data['short_pe']} PE"
        
        with open(MARKDOWN_JOURNAL, "a", encoding="utf-8") as f:
            f.write(f"| {trade_data['date']} | {trade_data['day_name']} | `{trade_data['mode']}` | {trade_data['spot']:,.0f} | {strikes_str} | {trade_data['exit_reason']} | **{pts_str}** | **{pnl_str}** |\n")

        print(f"[+] Journaled trade to CSV and {MARKDOWN_JOURNAL}")
