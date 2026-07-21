# -*- coding: utf-8 -*-
"""
Force printer settings to windows and 58mm
"""
import sys
from pathlib import Path
import sqlite3

def force_settings():
    db_path = Path("data/database.db")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('printer_type', 'windows')")
        cursor.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('paper_size', '58mm')")
        conn.commit()
        conn.close()
        print("Forced GDI settings.")

if __name__ == "__main__":
    force_settings()
