# -*- coding: utf-8 -*-
"""
Verification test script for Splash Screen & Hard Reset stability fixes.
"""

import sys
import os
import time
import tempfile
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import DatabaseManager
from utils.system_utils import cleanup_resources

def test_database_manager_auto_init():
    print("=== Test 1: Testing DatabaseManager Auto-Init on Fresh File ===")
    test_db_path = BASE_DIR / "temp" / "test_fresh_init.db"
    if test_db_path.exists():
        test_db_path.unlink()
        
    db = DatabaseManager(db_path=str(test_db_path))
    assert db.initialize_database() is True, "Database initialization failed"
    assert test_db_path.exists(), "DB file was not created"
    
    # Verify tables exist
    db.connect()
    users = db.fetch_all("SELECT username FROM users")
    db.disconnect()
    assert len(users) >= 1, "Admin user missing from fresh DB"
    print("✅ Test 1 Passed: Database initialized cleanly without recursive loop!")

def test_hard_reset_sequence():
    print("\n=== Test 2: Testing Hard Reset Sequence ===")
    test_db_path = BASE_DIR / "temp" / "test_hard_reset.db"
    
    # Step 1: Initialize DB
    db = DatabaseManager(db_path=str(test_db_path))
    db.initialize_database()
    assert test_db_path.exists(), "DB file missing before reset"
    
    # Step 2: Simulate Hard Reset in SettingsWindow
    DatabaseManager.close_all_connections()
    
    for suffix in ["", "-wal", "-shm"]:
        f_path = Path(str(test_db_path) + suffix)
        if f_path.exists():
            f_path.unlink()
            
    assert not test_db_path.exists(), "DB file was not unlinked"
    assert DatabaseManager._schema_upgraded is False, "Schema upgraded flag not reset"
    assert DatabaseManager._is_initializing is False, "Initializing flag not reset"
    
    # Step 3: Re-initialize after Hard Reset (simulating restart startup)
    db2 = DatabaseManager(db_path=str(test_db_path))
    assert db2.initialize_database() is True, "Re-initialization after hard reset failed"
    assert test_db_path.exists(), "DB file missing after re-initialization"
    
    # Cleanup test file
    DatabaseManager.close_all_connections()
    if test_db_path.exists():
        test_db_path.unlink()
        
    print("✅ Test 2 Passed: Hard Reset and re-initialization completed successfully!")

if __name__ == "__main__":
    try:
        os.makedirs(BASE_DIR / "temp", exist_ok=True)
        test_database_manager_auto_init()
        test_hard_reset_sequence()
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
