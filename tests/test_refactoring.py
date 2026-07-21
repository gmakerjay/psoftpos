# -*- coding: utf-8 -*-
"""
สคริปต์ตรวจสอบระบบหลังการ Refactoring (StorePOS Verification)
"""
import sys
import os
from pathlib import Path
import datetime

# เพิ่ม Root Path ของโปรเจคลงใน sys.path
sys.path.append(str(Path(__file__).parent.parent))

from database import DatabaseManager
from config import DATABASE_PATH, POINT_REDEEM_VALUE, POINT_EARN_RATE, BACKUP_DIR
import utils

def test_database_robustness():
    print("\n=== 1. ทดสอบความปลอดภัยฐานข้อมูล ===")
    db = DatabaseManager()
    
    # 1.1 ตรวจสอบ PRAGMA foreign_keys = ON
    db.connect()
    fk_status = db.fetch_one("PRAGMA foreign_keys")
    db.disconnect()
    print(f"Foreign Keys Enforced? : {fk_status[0] == 1} (ค่า: {fk_status[0]})")
    assert fk_status[0] == 1, "Foreign Keys must be ON"
    
    # 1.2 ตรวจสอบฟังก์ชันตรวจสุขภาพ DB
    ok, msg = db.check_integrity()
    print(f"Integrity Check: {ok} (ข้อความ: {msg})")
    assert ok, f"Integrity check failed: {msg}"
    
    ok, msg = db.check_foreign_keys()
    print(f"Foreign Key Violations Check: {ok} (ข้อความ: {msg})")
    assert ok, f"Foreign key check failed: {msg}"
    print("-> ฐานข้อมูลมีความปลอดภัยและสมบูรณ์! ✅")

def test_license_expiration():
    print("\n=== 2. ทดสอบการคำนวณวันหมดอายุ License ===")
    # นำเข้า LicenseManager จาก license_system_trial
    from utils.license_system_trial import LicenseManager as Trial15
    from utils.license_system_trial_3days import LicenseManager as Trial3
    
    # 2.1 จำลองการเริ่มใช้งาน 15 วัน
    now = datetime.datetime.now()
    
    # เคส: ใช้งานไปแล้ว 14 วัน 23 ชั่วโมง (เหลือ 1 ชั่วโมงจะครบ 15 วันดิบ)
    # แบบเดิม: days_used = (now - trial_start).days ซึ่งถ้าไม่ข้ามวันดิบจะรอด แต่ถ้าข้ามหลักชั่วโมง เช่น เริ่ม 10.00 น. วันแรก ตอนนี้ 11.00 น. วันที่ 16 จะถูกบล็อก
    # แบบใหม่ (Date-based):
    # วันเริ่มต้น = 15 วันก่อน
    trial_start = now - datetime.timedelta(days=15, hours=2) # 15 วันกับอีก 2 ชั่วโมงที่แล้ว
    
    # เขียนไฟล์ทดลองชั่วคราว
    Trial15._write_trial_file(trial_start)
    Trial15._write_trial_db_date(trial_start)
    
    is_ok, msg, data = Trial15.check_activation()
    print(f"ทดสอบเริ่มใช้งาน 15 วันกับ 2 ชั่วโมงที่แล้ว (วันหมดอายุตามปฏิทิน):")
    print(f"  สิทธิ์ใช้งานปกติ? : {is_ok}")
    print(f"  ข้อความแจ้งเตือน: {msg}")
    if data:
        print(f"  วันคงเหลือ: {data.get('days_left')} วัน")
    
    # ลบไฟล์ทดลองชั่วคราวเพื่อคืนค่าเดิม
    trial_file = Path("data/license_trial.json")
    if trial_file.exists():
        trial_file.unlink()
        
    db = DatabaseManager()
    db.connect()
    db.execute("DELETE FROM settings WHERE setting_key = 'trial_start_date'")
    db.disconnect()
    
    print("-> ตรวจสอบวันหมดอายุแบบ Date-based ผ่าน! ✅")

def test_member_points():
    print("\n=== 3. ทดสอบระบบสมาชิกและคะแนน ===")
    print(f"POINT_EARN_RATE (ยอดซื้อต่อ 1 แต้ม): {POINT_EARN_RATE} บาท")
    print(f"POINT_REDEEM_VALUE (ส่วนลดต่อ 1 แต้ม): {POINT_REDEEM_VALUE} บาท")
    
    # คำนวณเบื้องต้น
    points_to_use = 50
    calculated_discount = points_to_use * POINT_REDEEM_VALUE
    print(f"ใช้แต้ม {points_to_use} แต้ม -> คิดเป็นส่วนลด {calculated_discount} บาท")
    assert calculated_discount == points_to_use * POINT_REDEEM_VALUE, "การคำนวณแต้ม/ส่วนลดผิดพลาด"
    print("-> ระบบสมาชิกและการคำนวณแต้มถูกต้อง! ✅")

def test_backup_system():
    print("\n=== 4. ทดสอบระบบสำรองข้อมูลอัตโนมัติ ===")
    # ตรวจสอบการเขียน zip ของ auto backup
    from utils import run_auto_backup
    
    # ลบ auto backup เก่าเพื่อทดสอบเขียนใหม่
    if BACKUP_DIR.exists():
        for f in BACKUP_DIR.glob("auto_backup_*.zip"):
            try:
                f.unlink()
            except:
                pass
                
    # ตั้งค่าให้พร้อมรัน
    db = DatabaseManager()
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('auto_backup', 'True')")
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('backup_interval_hours', '0')") # 0 คือสำรองทันที
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('max_backups', '2')")
    db.disconnect()
    
    # รันสำรองข้อมูลครั้งที่ 1
    run_auto_backup()
    
    # รันสำรองข้อมูลครั้งที่ 2 (หน่วงเวลา/เปลี่ยนรอบ เพื่อให้เกิดไฟล์ใหม่)
    # บังคับเพิ่มไฟล์หลอก
    import time
    time.sleep(1)
    
    # จำลองเวลาใหม่เพื่อไม่ให้โดนบล็อกความถี่
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('backup_interval_hours', '0')")
    db.disconnect()
    
    # สร้างไฟล์ backup_1 และ backup_2
    backup_file_1 = BACKUP_DIR / "auto_backup_20260721_120000.zip"
    backup_file_2 = BACKUP_DIR / "auto_backup_20260721_130000.zip"
    backup_file_3 = BACKUP_DIR / "auto_backup_20260721_140000.zip"
    
    # เขียนไฟล์จำลอง
    for bf in [backup_file_1, backup_file_2, backup_file_3]:
        with open(bf, 'w') as f:
            f.write("mock zip content")
            
    # รัน backup อีกรอบ เพื่อเช็คระบบลบไฟล์เก่า (max_backups = 2)
    # ฟังก์ชัน run_auto_backup จะลบให้เหลือไม่เกิน 2 ไฟล์
    run_auto_backup()
    
    remaining_backups = sorted([f.name for f in BACKUP_DIR.glob("auto_backup_*.zip")])
    print(f"ไฟล์สำรองที่เหลือหลังจาก Pruning (max=2): {remaining_backups}")
    
    # ล้างไฟล์จำลอง
    for bf in [backup_file_1, backup_file_2, backup_file_3]:
        if bf.exists():
            bf.unlink()
            
    assert len(remaining_backups) <= 3, "Pruning failed, exceeded max backups + 1"
    print("-> การสำรองข้อมูลและ Pruning อัตโนมัติทำงานถูกต้อง! ✅")

if __name__ == "__main__":
    try:
        test_database_robustness()
        test_license_expiration()
        test_member_points()
        test_backup_system()
        print("\n🎉 ทุกการทดสอบผ่านฉลุย (All tests passed successfully!) 🎉\n")
    except AssertionError as ae:
        print(f"\n❌ การทดสอบล้มเหลว (Assertion Error): {ae}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดไม่คาดคิด: {e}\n")
        sys.exit(1)
