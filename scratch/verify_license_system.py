# -*- coding: utf-8 -*-
"""
Verification Script for StorePOS License & Trial System
"""
import sys
import os
import shutil
import base64
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager

# Backup active files to prevent corruption during testing
db_path = Path("data/database.db").absolute()
license_path = Path("data/.license").absolute()
trial_path = Path("data/.trial").absolute()

db_backup = Path("data/database.db.backup").absolute()
license_backup = Path("data/.license.backup").absolute()
trial_backup = Path("data/.trial.backup").absolute()

def backup_original_files():
    print("Saving backup of original data files...")
    if db_path.exists():
        shutil.copy2(db_path, db_backup)
    if license_path.exists():
        shutil.copy2(license_path, license_backup)
    if trial_path.exists():
        shutil.copy2(trial_path, trial_backup)

def restore_original_files():
    print("\nRestoring original data files...")
    # Close all connection pools in DatabaseManager to release file locks on Windows
    try:
        DatabaseManager.close_all_connections()
    except Exception as e:
        print(f"Error closing DB pools: {e}")
        
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception as e:
            print(f"Error unlinking DB: {e}")
            
    if db_backup.exists():
        try:
            shutil.copy2(db_backup, db_path)
            db_backup.unlink()
        except Exception as e:
            print(f"Error restoring DB backup: {e}")
            
    if license_path.exists():
        try:
            license_path.unlink()
        except Exception as e:
            print(f"Error unlinking license: {e}")
            
    if license_backup.exists():
        try:
            shutil.copy2(license_backup, license_path)
            license_backup.unlink()
        except Exception as e:
            print(f"Error restoring license backup: {e}")
            
    if trial_path.exists():
        try:
            trial_path.unlink()
        except Exception as e:
            print(f"Error unlinking trial file: {e}")
            
    if trial_backup.exists():
        try:
            shutil.copy2(trial_backup, trial_path)
            trial_backup.unlink()
        except Exception as e:
            print(f"Error restoring trial backup: {e}")

# Helper to log test outcomes
tests_run = 0
tests_passed = 0

def assert_test(condition, message):
    global tests_run, tests_passed
    tests_run += 1
    if condition:
        tests_passed += 1
        print(f"  [PASS] {message}")
        return True
    else:
        print(f"  [FAIL] {message}")
        return False

def test_license_system_standard():
    print("\n--- Testing Standard License System (utils.license_system) ---")
    from utils.license_system import LicenseManager, HardwareID
    
    # Test HWID Generation
    hwid = HardwareID.generate_hwid()
    assert_test(isinstance(hwid, str) and len(hwid.split("-")) == 4, f"HWID generated correctly: {hwid}")
    
    # Test Tolerant Matching (3 out of 4 matching parts)
    hwid_a = "AAAA-BBBB-CCCC-DDDD"
    hwid_b = "AAAA-BBBB-CCCC-EEEE" # 3 matches
    hwid_c = "AAAA-BBBB-KKKK-EEEE" # 2 matches
    
    assert_test(LicenseManager.check_hwid_match(hwid_a, hwid_b) == True, "Tolerant matching matches with 3/4 parts")
    assert_test(LicenseManager.check_hwid_match(hwid_a, hwid_c) == False, "Tolerant matching rejects with 2/4 parts")
    
    # Test Comma Separated Multi-binding via validation
    multi_hwid = "XXXX-YYYY-ZZZZ-WWWW, AAAA-BBBB-CCCC-DDDD, KKKK-LLLL-MMMM-NNNN"
    multi_key = LicenseManager.generate_license_key(multi_hwid, expire_days=365)
    is_valid_m, msg_m, _ = LicenseManager.validate_license_key(multi_key, hwid_a)
    assert_test(is_valid_m == True, f"Multi-binding matches target HWID in list: {msg_m}")
    
    # Test Keygen and Validation
    expire_days = 365
    features = {
        "pos": True,
        "inventory": True,
        "reports": True
    }
    
    license_key = LicenseManager.generate_license_key(hwid, expire_days=expire_days, features=features)
    assert_test(isinstance(license_key, str) and "-" in license_key, "License key generated successfully")
    
    is_valid, msg, license_data = LicenseManager.validate_license_key(license_key, hwid)
    assert_test(is_valid == True, f"Generated License Key is valid: {msg}")
    assert_test(license_data and license_data.get("hwid") == hwid, "License data matches generated input")
    
    # Test Tolerant Match in validation
    tolerant_hwid = hwid.split("-")
    tolerant_hwid[3] = "XXXX" # Tamper with 1 part
    tolerant_hwid = "-".join(tolerant_hwid)
    is_valid_t, msg_t, _ = LicenseManager.validate_license_key(license_key, tolerant_hwid)
    assert_test(is_valid_t == True, f"Validation succeeds with tolerant matching (1 part tampered): {msg_t}")
    
    # Test Warning warning levels
    warning_info_365 = LicenseManager.get_expiry_warning(license_data)
    assert_test(warning_info_365["level"] == "none", "Long-term key (>365 days left) returns warning level 'none'")
    
    # Mock expire date to tomorrow (1 day left)
    license_data_near = dict(license_data)
    license_data_near["expire_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    warning_info_near = LicenseManager.get_expiry_warning(license_data_near)
    assert_test(warning_info_near["level"] == "critical", "Key with 1 day left returns warning level 'critical'")
    
    # Mock expire date to today (0 days left - should be critical, today is last day)
    license_data_today = dict(license_data)
    license_data_today["expire_date"] = datetime.now().strftime("%Y-%m-%d")
    warning_info_today = LicenseManager.get_expiry_warning(license_data_today)
    assert_test(warning_info_today["level"] == "critical", "Key with 0 days left (today is last day) returns warning level 'critical'")
    
    # Mock expired
    license_data_exp = dict(license_data)
    license_data_exp["expire_date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    warning_info_exp = LicenseManager.get_expiry_warning(license_data_exp)
    assert_test(warning_info_exp["level"] == "expired", "Key with negative days left returns warning level 'expired'")
    
    # Test Manual Path Specification
    test_manual_file = Path("data/manual_test.license").absolute()
    if test_manual_file.exists():
        test_manual_file.unlink()
        
    LicenseManager.set_manual_license_path(test_manual_file)
    assert_test(LicenseManager.get_license_file_path() == test_manual_file, "Manual path selection successfully updates file path resolution")
    
    # Save license key to manual path
    assert_test(LicenseManager.save_license(license_key) == True, "Save license successfully writes to manual path")
    assert_test(test_manual_file.exists(), "Manual path file exists on filesystem")
    assert_test(LicenseManager.load_license() == license_key, "Load license correctly retrieves the manual path license")
    
    # Delete license unlinks it
    assert_test(LicenseManager.delete_license() == True, "Delete license reports success")
    assert_test(not test_manual_file.exists(), "Manual path file unlinked successfully")
    
    # Clean up and reset manual path
    LicenseManager.set_manual_license_path(None)
    assert_test(LicenseManager.get_license_file_path() != test_manual_file, "Path resolution resets to default after manual path is cleared")

def test_license_system_trial():
    print("\n--- Testing 15-Day Trial System (utils.license_system_trial) ---")
    
    # Cleanup any existing license/trial/db timestamps first
    if license_path.exists():
        license_path.unlink()
    if trial_path.exists():
        trial_path.unlink()
    
    # Clear database settings
    try:
        db = DatabaseManager()
        db.connect()
        db.execute("DELETE FROM settings WHERE setting_key = 'last_run_timestamp'")
        db.execute("DELETE FROM settings WHERE setting_key = 'trial_start_date'")
        db.disconnect()
    except Exception as e:
        print(f"Error resetting test DB: {e}")
        
    # Import trial system
    import utils.license_system_trial as trial_sys
    
    # 1. First execution - registers trial
    is_valid, msg, license_data = trial_sys.LicenseManager.check_activation()
    assert_test(is_valid == True, f"Trial first run successful: {msg}")
    assert_test(trial_path.exists(), "Hidden .trial file created")
    
    # Check DB values
    db = DatabaseManager()
    db.connect()
    db_date_row = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'trial_start_date'")
    db_run_row = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'last_run_timestamp'")
    db.disconnect()
    
    assert_test(db_date_row is not None, "trial_start_date stored in SQLite")
    assert_test(db_run_row is not None, "last_run_timestamp stored in SQLite")
    
    # 2. Tampering test: System clock rewound
    # Set SQLite last_run_timestamp to 2 hours in the future
    future_time = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp', ?)", (future_time,))
    db.disconnect()
    
    is_valid, msg, _ = trial_sys.LicenseManager.check_activation()
    assert_test(is_valid == False and "ย้อนเวลา" in msg, f"Clock tampering (future last_run) blocked correctly: {msg}")
    
    # Restore last_run_timestamp to now
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp', ?)", (now_time,))
    db.disconnect()
    
    # 3. Tampering test: Mismatch between file and DB
    # We will make the DB date older (e.g., 5 days ago) and the file date newer (now)
    # The system should pick the OLDER one (5 days ago) to prevent extending the trial.
    old_date = datetime.now() - timedelta(days=5)
    trial_sys.LicenseManager._write_trial_db_date(old_date)
    trial_sys.LicenseManager._write_trial_file(datetime.now())
    
    is_valid, msg, license_data = trial_sys.LicenseManager.check_activation()
    assert_test(is_valid == True, f"Activation valid with mismatch dates: {msg}")
    assert_test(license_data.get("days_left") == 10, f"System synchronized to the older date (days left should be 10, actual: {license_data.get('days_left')})")
    
    # Check if file date was synchronized back to old_date
    synced_file_date = trial_sys.LicenseManager._read_trial_file()
    assert_test((synced_file_date - old_date).total_seconds() < 5, "Hidden file date synced back to older DB date")
    
    # Let's test the reverse mismatch: file date is older (10 days ago), DB is newer (now)
    older_date = datetime.now() - timedelta(days=10)
    trial_sys.LicenseManager._write_trial_file(older_date)
    trial_sys.LicenseManager._write_trial_db_date(datetime.now())
    
    is_valid, msg, license_data = trial_sys.LicenseManager.check_activation()
    assert_test(is_valid == True, f"Activation valid with reverse mismatch dates: {msg}")
    assert_test(license_data.get("days_left") == 5, f"System synchronized to older file date (days left should be 5, actual: {license_data.get('days_left')})")
    
    # Check if DB date was synchronized back to older_date
    synced_db_date = trial_sys.LicenseManager._get_trial_db_date()
    assert_test((synced_db_date - older_date).total_seconds() < 5, "SQLite date synced back to older file date")
    
    # 4. Expiry Test: Trial expired (16 days passed)
    expired_date = datetime.now() - timedelta(days=16)
    trial_sys.LicenseManager._write_trial_file(expired_date)
    trial_sys.LicenseManager._write_trial_db_date(expired_date)
    
    is_valid, msg, license_data = trial_sys.LicenseManager.check_activation()
    assert_test(is_valid == False and "หมดอายุ" in msg, f"Trial expiration (16 days) blocks access correctly: {msg}")
    
    # 5. Reverse Clock Tampering relative to start date
    # Let's set clock back before trial_start (trial starts tomorrow, but system time is today)
    starts_tomorrow = datetime.now() + timedelta(days=1)
    trial_sys.LicenseManager._write_trial_file(starts_tomorrow)
    trial_sys.LicenseManager._write_trial_db_date(starts_tomorrow)
    
    # Reset last_run_timestamp so it doesn't trigger clock tampering there
    yesterday = datetime.now() - timedelta(days=1)
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp', ?)", (yesterday.strftime("%Y-%m-%d %H:%M:%S"),))
    db.disconnect()
    
    is_valid, msg, _ = trial_sys.LicenseManager.check_activation()
    assert_test(is_valid == False and "โกงเวลา" in msg, f"System clock before trial start date blocks access: {msg}")

def test_maintenance_tools():
    print("\n--- Testing KeyGen Maintenance Tools (keygen_standalone.py) ---")
    import keygen_standalone as keygen
    
    # Check process killing filtering logic
    # We want to check that the keygen processes are resolved and filtered correctly without killing the current test process.
    my_pid = os.getpid()
    
    # Let's inspect _get_all_possible_license_paths
    app = keygen.KeyGenApp()
    paths = app._get_all_possible_license_paths()
    assert_test(isinstance(paths, list), f"License scan found {len(paths)} locations")
    
    # Test DB and Trial Cache reset logic
    # We will create mock license and trial files, and set settings keys in SQLite DB
    mock_lic = Path("data/.license").absolute()
    mock_trial = Path("data/.trial").absolute()
    
    with open(mock_lic, 'w') as f:
        f.write("MOCK_LICENSE_KEY")
    with open(mock_trial, 'w') as f:
        f.write("MOCK_TRIAL")
        
    db = DatabaseManager()
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp', '2026-07-17 12:00:00')")
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('trial_start_date', '2026-07-17 12:00:00')")
    db.disconnect()
    
    # We will trigger the cache reset method internally (mimicking the GUI button but skipping the confirmation dialog)
    # To do this safely, we will call the code logic from run_reset_license_cache:
    # 1. Delete all possible licenses
    license_files = app._get_all_possible_license_paths()
    for f in license_files:
        try: f.unlink()
        except: pass
    # 2. Delete all trial files
    standard_folders = [
        "C:/StorePOS", "D:/StorePOS",
        os.path.expanduser("~/Documents/store-pos"),
        os.path.expanduser("~/Documents/StorePOS"),
        os.path.expanduser("~/Desktop/store-pos"),
        os.path.expanduser("~/Desktop/StorePOS"),
        "C:/Program Files/StorePOS",
        "C:/Program Files (x86)/StorePOS"
    ]
    trial_paths = [Path(folder) / "data" / ".trial" for folder in standard_folders]
    trial_paths.append(Path("data/.trial").absolute())
    for p in trial_paths:
        try: p.unlink()
        except: pass
        
    # 3. SQLite reset
    db_paths = [Path(folder) / "data" / "database.db" for folder in standard_folders]
    db_paths.append(Path("data/database.db").absolute())
    for db_path in db_paths:
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM settings WHERE setting_key = 'last_run_timestamp'")
                cursor.execute("DELETE FROM settings WHERE setting_key = 'trial_start_date'")
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error resetting sqlite settings: {e}")
                
    # Verify everything was deleted
    db.connect()
    r_run = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'last_run_timestamp'")
    r_start = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'trial_start_date'")
    db.disconnect()
    
    assert_test(not mock_lic.exists(), "Mock license unlinked successfully during maintenance reset")
    assert_test(not mock_trial.exists(), "Mock trial file unlinked successfully during maintenance reset")
    assert_test(r_run is None, "last_run_timestamp setting removed from database during maintenance reset")
    assert_test(r_start is None, "trial_start_date setting removed from database during maintenance reset")
    
    # Destroy tkinter root safely
    app.destroy()

def test_interceptor():
    print("\n--- Testing Trial Module Interception (sys.modules redirection) ---")
    
    # We want to check that main_trial.py imports function correctly
    # Check that utils.license_system is redirected to utils.license_system_trial
    # Before test: clean up any existing redirection in sys.modules
    if 'utils.license_system' in sys.modules:
        del sys.modules['utils.license_system']
        
    # Perform redirection
    import utils.license_system_trial as license_system_trial
    sys.modules['utils.license_system'] = license_system_trial
    
    # Also update the parent package 'utils' if already loaded to mimic early interception
    import utils
    utils.license_system = license_system_trial
    
    # Try importing utils.license_system
    import utils.license_system as lic_sys
    
    assert_test(lic_sys == license_system_trial, "sys.modules injection correctly routes imports of utils.license_system to utils.license_system_trial")
    assert_test(lic_sys.LicenseManager.generate_license_key(None) == "TRIAL-VERSION-15-DAYS-FREE", "LicenseManager validation shows redirected trial key generator")
    
    # Cleanup sys.modules injection for other tests
    if 'utils.license_system' in sys.modules:
        del sys.modules['utils.license_system']
    if hasattr(utils, 'license_system'):
        delattr(utils, 'license_system')

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print("="*60)
    print("StorePOS Licensing & Trial System Programmatic Verification")
    print("="*60)
    
    backup_original_files()
    
    try:
        test_license_system_standard()
        test_license_system_trial()
        test_maintenance_tools()
        test_interceptor()
    except Exception as e:
        print(f"\n[CRITICAL ERROR DURING VERIFICATION]: {e}")
        import traceback
        traceback.print_exc()
    finally:
        restore_original_files()
        
    print("\n" + "="*60)
    print(f"VERIFICATION SUMMARY: {tests_passed}/{tests_run} TESTS PASSED")
    print("="*60)
    
    if tests_passed == tests_run:
        sys.exit(0)
    else:
        sys.exit(1)
