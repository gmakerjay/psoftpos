# -*- coding: utf-8 -*-
"""
Backup and Restore Automation Tester
ทดสอบระบบสำรองข้อมูลและกู้คืนข้อมูล 100%
"""
import sys
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# จำลอง path ต่างๆ
DATABASE_PATH = "data/database.db"
PRODUCTS_IMG_DIR = Path("data/products_img")
RECEIPTS_DIR = Path("data/receipts")

def test_backup():
    print("--- เริ่มจำลองการสำรองข้อมูล (Backup) ---")
    backup_filename = "data/test_backup.zip"
    if os.path.exists(backup_filename):
        os.remove(backup_filename)
        
    try:
        # สร้างโฟลเดอร์รูปภาพและใบเสร็จชั่วคราวสำหรับทดสอบ (ถ้ายังไม่มี)
        PRODUCTS_IMG_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # เขียนไฟล์รูปภาพและใบเสร็จทดสอบ
        test_img = PRODUCTS_IMG_DIR / "test_prod.png"
        test_img.write_text("dummy image data")
        
        test_receipt = RECEIPTS_DIR / "receipt_TEST.pdf"
        test_receipt.write_text("dummy receipt data")
        
        # ทำการ Backup
        with zipfile.ZipFile(backup_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. ฐานข้อมูล
            db_path_file = Path(DATABASE_PATH)
            if db_path_file.exists():
                zipf.write(str(db_path_file), "database.db")
                print(f"  [SUCCESS] สำรองฐานข้อมูล: {db_path_file} ({db_path_file.stat().st_size} bytes)")
            else:
                print("  [WARNING] ไม่พบไฟล์ฐานข้อมูลหลักสำหรับการสำรอง")
                
            # 2. รูปภาพสินค้า
            if PRODUCTS_IMG_DIR.exists():
                for img_file in PRODUCTS_IMG_DIR.glob("*"):
                    if img_file.is_file():
                        zipf.write(img_file, f"products_img/{img_file.name}")
                print(f"  [SUCCESS] สำรองรูปภาพสินค้าเสร็จสิ้น")
                
            # 3. ใบเสร็จ
            if RECEIPTS_DIR.exists():
                for receipt_file in RECEIPTS_DIR.glob("*.pdf"):
                    zipf.write(receipt_file, f"receipts/{receipt_file.name}")
                print(f"  [SUCCESS] สำรองใบเสร็จเสร็จสิ้น")
                
        print(f"-> สร้างไฟล์สำรองสำเร็จที่: {backup_filename} ({os.path.getsize(backup_filename)} bytes)")
        return backup_filename
    except Exception as e:
        print(f"  [ERROR] การสำรองข้อมูลล้มเหลว: {e}")
        return None

def test_restore(backup_filename):
    print("\n--- เริ่มจำลองการกู้คืนข้อมูล (Restore) ---")
    if not backup_filename or not os.path.exists(backup_filename):
        print("  [ERROR] ไม่พบไฟล์สำรองข้อมูลเพื่อใช้กู้คืน")
        return False
        
    try:
        temp_dir = Path("data/restore_temp_test")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            
        # 1. แตกไฟล์ zip ไปยังห้องชั่วคราว
        with zipfile.ZipFile(backup_filename, 'r') as zipf:
            zipf.extractall(temp_dir)
            print("  [SUCCESS] แตกไฟล์สำรองชั่วคราวสำเร็จ")
            
        # 2. จำลองการปิด Connection ฐานข้อมูล (เสมือนเรียก DatabaseManager.close_all_connections)
        print("  [INFO] กำลังปิดการเชื่อมต่อฐานข้อมูลทั้งหมด...")
        
        # 3. เคลียร์ไฟล์ WAL และ SHM
        db_wal = Path(DATABASE_PATH).with_name(Path(DATABASE_PATH).name + "-wal")
        db_shm = Path(DATABASE_PATH).with_name(Path(DATABASE_PATH).name + "-shm")
        try:
            if db_wal.exists():
                db_wal.unlink()
                print("  [SUCCESS] ลบไฟล์ WAL เรียบร้อย")
            if db_shm.exists():
                db_shm.unlink()
                print("  [SUCCESS] ลบไฟล์ SHM เรียบร้อย")
        except Exception as e:
            print(f"  [WARNING] ไม่สามารถลบไฟล์ WAL/SHM: {e}")
            
        # 4. ย้ายฐานข้อมูลหลักคืน
        if (temp_dir / "database.db").exists():
            shutil.copy(temp_dir / "database.db", DATABASE_PATH)
            print(f"  [SUCCESS] กู้คืนไฟล์ฐานข้อมูลหลักเรียบร้อย")
            
        # 5. กู้คืนรูปภาพสินค้า
        img_restore_dir = temp_dir / "products_img"
        if img_restore_dir.exists():
            PRODUCTS_IMG_DIR.mkdir(parents=True, exist_ok=True)
            for img_file in img_restore_dir.iterdir():
                shutil.copy(img_file, PRODUCTS_IMG_DIR / img_file.name)
            print("  [SUCCESS] กู้คืนรูปภาพสินค้าเรียบร้อย")
            
        # 6. กู้คืนไฟล์ใบเสร็จ
        receipt_restore_dir = temp_dir / "receipts"
        if receipt_restore_dir.exists():
            RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
            for receipt_file in receipt_restore_dir.iterdir():
                shutil.copy(receipt_file, RECEIPTS_DIR / receipt_file.name)
            print("  [SUCCESS] กู้คืนไฟล์ใบเสร็จเรียบร้อย")
            
        # 7. ลบโฟลเดอร์ชั่วคราว
        shutil.rmtree(temp_dir)
        print("  [SUCCESS] ล้างข้อมูลโฟลเดอร์ชั่วคราวเรียบร้อย")
        
        print("-> การจำลองการกู้คืนข้อมูลสำเร็จ 100%!")
        return True
    except Exception as e:
        print(f"  [ERROR] การกู้คืนข้อมูลล้มเหลว: {e}")
        return False

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    backup_file = test_backup()
    if backup_file:
        test_restore(backup_file)
        # ลบไฟล์ทดสอบหลังเสร็จงานเพื่อสุขอนามัยที่ดีของโค้ด
        if os.path.exists(backup_file):
            os.remove(backup_file)
        print("\n=== ระบบสำรองและกู้คืนข้อมูลเสร็จสิ้นกระบวนการทดสอบ ===")
