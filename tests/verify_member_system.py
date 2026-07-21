# -*- coding: utf-8 -*-
"""
Verification Script for Member & Points System
"""
import sys
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager

# Backup active files to prevent corruption during testing
db_path = Path("data/database.db").absolute()
db_backup = Path("data/database.db.backup").absolute()

def backup_original_files():
    print("Saving backup of database file...")
    if db_path.exists():
        shutil.copy2(db_path, db_backup)

def restore_original_files():
    print("\nRestoring original database file...")
    try:
        DatabaseManager.close_all_connections()
    except Exception as e:
        print(f"Error closing DB connections: {e}")
        
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

def test_database_schema():
    print("\n--- Testing Database Schema Upgrades ---")
    db = DatabaseManager()
    db.connect()
    
    # 1. Check columns in members table
    db.cursor.execute("PRAGMA table_info(members)")
    members_cols = [col[1] for col in db.cursor.fetchall()]
    assert_test("address" in members_cols, "members table contains 'address' column")
    assert_test("privilege" in members_cols, "members table contains 'privilege' column")
    
    # 2. Check columns in sales table
    db.cursor.execute("PRAGMA table_info(sales)")
    sales_cols = [col[1] for col in db.cursor.fetchall()]
    assert_test("points_earned" in sales_cols, "sales table contains 'points_earned' column")
    assert_test("points_used" in sales_cols, "sales table contains 'points_used' column")
    
    db.disconnect()

def test_member_crud():
    print("\n--- Testing Simplified Member CRUD Operations ---")
    db = DatabaseManager()
    db.connect()
    
    # 1. Insert a new simplified member
    name = "นายทดสอบ รักดี"
    phone = "0812345678"
    address = "123/45 ถนนพัฒนาการ แขวงสวนหลวง กรุงเทพฯ"
    privilege = "ส่งฟรีไม่มีขั้นต่ำ, ส่วนลดท้ายบิล 5%"
    points = 150
    
    # Fetch general tier ID
    gen_tier = db.fetch_one("SELECT tier_id FROM member_tiers WHERE tier_name LIKE '%General%'")
    tier_id = gen_tier['tier_id'] if gen_tier else 1
    
    success = db.execute("""
        INSERT INTO members (name, phone, address, privilege, points, tier_id, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    """, (name, phone, address, privilege, points, tier_id))
    assert_test(success == True, "Test member inserted successfully")
    
    # 2. Query and verify the member details
    member = db.fetch_one("SELECT * FROM members WHERE phone = ?", (phone,))
    assert_test(member is not None, "Test member found by phone number")
    if member:
        assert_test(member['name'] == name, f"Name matches: {member['name']}")
        assert_test(member['address'] == address, f"Address matches: {member['address']}")
        assert_test(member['privilege'] == privilege, f"Privilege matches: {member['privilege']}")
        assert_test(member['points'] == points, f"Initial points matches: {member['points']}")
    
    # 3. Update the member details
    new_points = 250
    new_address = "456/78 ถนนสุขุมวิท กรุงเทพฯ"
    update_success = db.execute("""
        UPDATE members SET points = ?, address = ? WHERE member_id = ?
    """, (new_points, new_address, member['member_id']))
    assert_test(update_success == True, "Member updated successfully")
    
    updated_member = db.fetch_one("SELECT * FROM members WHERE member_id = ?", (member['member_id'],))
    if updated_member:
        assert_test(updated_member['points'] == new_points, f"Updated points matches: {updated_member['points']}")
        assert_test(updated_member['address'] == new_address, f"Updated address matches: {updated_member['address']}")
        
    db.disconnect()

def test_pos_points_checkout():
    print("\n--- Testing POS Points Accumulation & Redemption ---")
    db = DatabaseManager()
    db.connect()
    
    # Load member
    member = db.fetch_one("SELECT * FROM members WHERE phone = '0812345678'")
    member_id = member['member_id']
    initial_points = member['points'] # should be 250
    
    # Simulate a checkout:
    # Subtotal: 1500 THB. Discount: 0. VAT: 0. Total: 1500 THB.
    # Points to earn: 1500 // 100 = 15 points.
    # Points to redeem/use: 50 points.
    total = 1500.00
    points_used = 50
    points_earned = int(total // 100) # 15 points
    
    sale_number = "TX-TEST-POINTS"
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = 1
    
    # Start transaction
    db.begin_transaction()
    try:
        # Save sale
        db.execute("""
            INSERT INTO sales (
                sale_number, sale_date, user_id, price_type,
                subtotal, discount_type, discount_value, discount_amount,
                tax_amount, total_amount, paid_amount, change_amount,
                payment_method, status, member_id, points_earned, points_used
            ) VALUES (?, ?, ?, 'retail', ?, 'none', 0, 0, 0, ?, ?, 0, 'cash', 'completed', ?, ?, ?)
        """, (sale_number, sale_date, user_id, total, total, total, member_id, points_earned, points_used))
        
        # Deduct used points and add earned points
        db.execute("""
            UPDATE members SET points = MAX(0, points - ? + ?) WHERE member_id = ?
        """, (points_used, points_earned, member_id))
        
        db.commit_transaction()
        print("  Simulated points checkout database transaction completed")
    except Exception as e:
        db.rollback_transaction()
        print(f"  [ERROR] Database transaction failed: {e}")
        
    # Verify member points are updated
    updated_member = db.fetch_one("SELECT points FROM members WHERE member_id = ?", (member_id,))
    expected_points = initial_points - points_used + points_earned # 250 - 50 + 15 = 215
    assert_test(updated_member['points'] == expected_points, f"Member points balance correctly updated: actual={updated_member['points']}, expected={expected_points}")
    
    # Verify sales record contains points audit trail
    sale_record = db.fetch_one("SELECT points_earned, points_used FROM sales WHERE sale_number = ?", (sale_number,))
    assert_test(sale_record is not None, "Sales record found in database")
    if sale_record:
        assert_test(sale_record['points_earned'] == points_earned, f"Sale points_earned correct: {sale_record['points_earned']}")
        assert_test(sale_record['points_used'] == points_used, f"Sale points_used correct: {sale_record['points_used']}")
        
    # Verify member history view query returns correct data
    history = db.fetch_all("""
        SELECT s.sale_number, s.points_earned, s.points_used
        FROM sales s
        WHERE s.member_id = ?
        ORDER BY s.sale_date DESC
    """, (member_id,))
    assert_test(len(history) >= 1, f"Purchase history log retrieved successfully (records found: {len(history)})")
    if history:
        assert_test(history[0]['points_earned'] == points_earned and history[0]['points_used'] == points_used, "History points earned/used align with invoice log")
        
    db.disconnect()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print("="*60)
    print("StorePOS Customer Member & Points System Verification")
    print("="*60)
    
    backup_original_files()
    
    # Trigger database upgrades on startup
    try:
        db = DatabaseManager()
        db.connect()
        # Trigger schema upgrade manually
        db._upgrade_database_schema()
        db.disconnect()
        
        test_database_schema()
        test_member_crud()
        test_pos_points_checkout()
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
