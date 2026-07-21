import os
import sqlite3
from pathlib import Path

trial_file = Path("data/.trial_3days")
if trial_file.exists():
    trial_file.unlink()
    print("Deleted 3-day trial file.")

db_file = Path("data/database.db")
if db_file.exists():
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM settings WHERE setting_key IN ('trial_start_date_3days', 'last_run_timestamp_3days')")
        conn.commit()
        conn.close()
        print("Cleared 3-day trial database keys.")
    except Exception as e:
        print(f"Error clearing DB keys: {e}")
