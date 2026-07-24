# -*- coding: utf-8 -*-
import os
import sqlite3
import winreg
import base64
from datetime import datetime

# Reset start date to NOW
now = datetime.now()
dt_str = now.strftime("%Y-%m-%d %H:%M:%S")
encoded = base64.b64encode(dt_str.encode()).decode()

print(f"[RESET] Setting trial start date to TODAY: {dt_str}")

# 1. Desktop File
f2 = 'c:/Users/admin/Desktop/StorePOS_30DayTrial/data/.trial_30days'
os.makedirs(os.path.dirname(f2), exist_ok=True)
with open(f2, 'w') as f:
    f.write(encoded)

# 2. Workspace File
f1 = 'c:/Users/admin/Documents/store-pos/data/.trial_30days'
os.makedirs(os.path.dirname(f1), exist_ok=True)
with open(f1, 'w') as f:
    f.write(encoded)

# 3. Desktop DB
db2_path = 'c:/Users/admin/Desktop/StorePOS_30DayTrial/data/database.db'
if os.path.exists(db2_path):
    conn = sqlite3.connect(db2_path)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('trial_start_date_30days', ?)", (encoded,))
    conn.commit()
    conn.close()

# 4. Workspace DB
db1_path = 'c:/Users/admin/Documents/store-pos/data/database.db'
if os.path.exists(db1_path):
    conn = sqlite3.connect(db1_path)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('trial_start_date_30days', ?)", (encoded,))
    conn.commit()
    conn.close()

# 5. Registry
try:
    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\PSoftPOS", 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "TrialData30", 0, winreg.REG_SZ, encoded)
    winreg.CloseKey(key)
except Exception:
    pass

print("==================================================")
print("RESET COMPLETE: Fresh 30-Day Trial Active!")
print("==================================================")
