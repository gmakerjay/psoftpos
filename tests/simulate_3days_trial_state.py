# -*- coding: utf-8 -*-
"""
Utility script to simulate 3-day Trial states for testing purposes.
Allows setting trial start date to today (active), 4 days ago (expired), or tomorrow (tampered).
"""
import base64
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import sys

# Add root folder to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TRIAL_FILE = Path("data/.trial_3days")
DB_FILE = Path("data/database.db")

def set_trial_date(days_ago):
    dt = datetime.now() - timedelta(days=days_ago)
    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    encoded = base64.b64encode(dt_str.encode()).decode()
    
    # 1. Write to hidden file
    TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRIAL_FILE, 'w') as f:
        f.write(encoded)
    print(f"[-] Wrote to {TRIAL_FILE}: {dt_str}")
    
    # 2. Write to SQLite DB
    TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True) # Ensure data dir exists
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (setting_key TEXT PRIMARY KEY, setting_value TEXT)")
    cursor.execute("""
        INSERT OR REPLACE INTO settings (setting_key, setting_value)
        VALUES ('trial_start_date_3days', ?)
    """, (encoded,))
    
    # Also reset last run timestamp to prevent clock tampering error
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO settings (setting_key, setting_value)
        VALUES ('last_run_timestamp_3days', ?)
    """, (now_str,))
    conn.commit()
    conn.close()
    print(f"[-] Updated settings in {DB_FILE} with start_date={dt_str}")

if __name__ == '__main__':
    print("====================================================")
    print("StorePOS 3-Day Trial Simulation Utility")
    print("====================================================")
    print("1. Set Trial Start to Today (3 Days Remaining)")
    print("2. Set Trial Start to 4 Days Ago (Expired Trial)")
    print("3. Set Trial Start to Tomorrow (Clock Tampering)")
    
    choice = sys.argv[1] if len(sys.argv) > 1 else '1'
    
    if choice == '1':
        set_trial_date(0)
        print("[SUCCESS] Trial reset to TODAY. Run 'python main_trial_3days.py' to test active trial!")
    elif choice == '2':
        set_trial_date(4)
        print("[SUCCESS] Trial set to 4 days ago (EXPIRED). Run 'python main_trial_3days.py' to test expired behavior!")
    elif choice == '3':
        set_trial_date(-1)
        print("[SUCCESS] Trial set to TOMORROW (TAMPERED). Run 'python main_trial_3days.py' to test clock tampering behavior!")
    else:
        print("[ERROR] Invalid choice.")
