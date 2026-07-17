import os
import shutil
from pathlib import Path

# Source paths
src_dist = Path(r"c:\Users\admin\Documents\store-pos\dist\StorePOS_3DayTrial")
src_db = Path(r"c:\Users\admin\Documents\store-pos\data\database.db")
src_keygen = Path(r"c:\Users\admin\Documents\store-pos\keygen_standalone.py")

# Destination paths
desktop = Path(r"C:\Users\admin\Desktop")
dest_root = desktop / "StorePOS_3DayTrial"
dest_prog = dest_root / "Program"
dest_tools = dest_root / "Tools"

print(f"Creating packaging structure in: {dest_root}")

# 1. Create structure
dest_prog.mkdir(parents=True, exist_ok=True)
dest_tools.mkdir(parents=True, exist_ok=True)

# 2. Copy compiled binary folder contents
if src_dist.exists():
    print("Copying compiled program files...")
    # Clean dest_prog first if it already has files
    for item in dest_prog.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
            
    # Copy directory contents
    for item in src_dist.iterdir():
        if item.is_dir():
            shutil.copytree(item, dest_prog / item.name)
        else:
            shutil.copy2(item, dest_prog / item.name)
else:
    print(f"[ERROR] Source dist folder not found: {src_dist}")

# 3. Create subfolders inside Program
(dest_prog / "Backup").mkdir(exist_ok=True)
(dest_prog / "Logs").mkdir(exist_ok=True)
(dest_prog / "Excel_Exports").mkdir(exist_ok=True)
(dest_prog / "data").mkdir(exist_ok=True)
(dest_prog / "data" / "products").mkdir(exist_ok=True)
(dest_prog / "data" / "backups").mkdir(exist_ok=True)

# 4. Copy database.db
if src_db.exists():
    print("Copying database file...")
    dest_db = dest_prog / "data" / "database.db"
    shutil.copy2(src_db, dest_db)
    
    # Ensure trial keys are cleared in the destination DB
    try:
        import sqlite3
        conn = sqlite3.connect(str(dest_db))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM settings WHERE setting_key IN ('trial_start_date_3days', 'last_run_timestamp_3days', 'trial_start_date', 'last_run_timestamp')")
        conn.commit()
        conn.close()
        print("Verified destination DB is clean of trial records.")
    except Exception as e:
        print(f"Error cleaning destination DB: {e}")
else:
    print(f"[WARNING] Database file not found at: {src_db}")

# 5. Clean up any trial activation files in destination
for f_name in [".trial", ".trial_3days", ".license", ".license_3days"]:
    f_path = dest_prog / "data" / f_name
    if f_path.exists():
        f_path.unlink()
        print(f"Removed trial/license file: {f_path}")

# 6. Copy keygen script to Tools
if src_keygen.exists():
    print("Copying KeyGen tool to Tools folder...")
    shutil.copy2(src_keygen, dest_tools / "keygen_standalone.py")

print("\nPackaging completed successfully!")
print(f"Standalone package path: {dest_root}")
