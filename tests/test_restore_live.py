# -*- coding: utf-8 -*-
"""
Live Backup & Restore Diagnostic Test
"""
import sys
from pathlib import Path
import shutil
import zipfile
from datetime import datetime

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, PRODUCTS_IMG_DIR

def run_test():
    print("=== เริ่มการตรวจสอบการทำงานของ Backup และ Restore ในสภาพแวดล้อมจริง ===")
    
    # 1. ทำการ Backup ข้อมูลจริงไปยัง live_backup.zip
    backup_zip = Path("data/live_backup.zip")
    if backup_zip.exists():
        backup_zip.unlink()
        
    try:
        db = DatabaseManager()
        db.connect()
        # ทำการสำรองข้อมูล
        with zipfile.ZipFile(str(backup_zip), 'w', zipfile.ZIP_DEFLATED) as zipf:
            db_path_file = Path(DATABASE_PATH)
            if db_path_file.exists():
                zipf.write(str(db_path_file), "database.db")
                
            img_dir = PRODUCTS_IMG_DIR
            if img_dir.exists():
                for img_file in img_dir.glob("*"):
                    if img_file.is_file():
                        zipf.write(img_file, f"products_img/{img_file.name}")
                        
            receipt_dir = Path("data/receipts")
            if receipt_dir.exists():
                for receipt_file in receipt_dir.glob("*.pdf"):
                    zipf.write(receipt_file, f"receipts/{receipt_file.name}")
                    
        print(f"  [SUCCESS] บันทึกไฟล์สำรองข้อมูลสดสำเร็จที่: {backup_zip.resolve()}")
    except Exception as e:
        print(f"  [ERROR] การสำรองข้อมูลสดล้มเหลว: {e}")
        return

    # 2. ทำการจำลองการ Restore ด้วยโค้ดเดียวกับใน settings_window.py
    print("=== เริ่มจำลองการกู้คืนข้อมูล (Restore) ===")
    try:
        # จำลองการแตกไฟล์ ZIP
        temp_dir = Path("data/restore_temp")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            
        with zipfile.ZipFile(str(backup_zip), 'r') as zipf:
            zipf.extractall(temp_dir)
            
        # ปิดการเชื่อมต่อ
        print("  - เรียก DatabaseManager.close_all_connections()")
        DatabaseManager.close_all_connections()
        
        # ลบไฟล์ WAL และ SHM
        try:
            db_wal = Path(DATABASE_PATH).with_name(Path(DATABASE_PATH).name + "-wal")
            db_shm = Path(DATABASE_PATH).with_name(Path(DATABASE_PATH).name + "-shm")
            if db_wal.exists():
                db_wal.unlink()
                print("  - ลบไฟล์ WAL สำเร็จ")
            if db_shm.exists():
                db_shm.unlink()
                print("  - ลบไฟล์ SHM สำเร็จ")
        except Exception as e:
            print(f"  [WARNING] เกิดข้อผิดพลาดขณะลบไฟล์ WAL/SHM: {e}")
            
        # คัดลอกฐานข้อมูลคืน
        print(f"  - กำลังคัดลอกไฟล์ {temp_dir / 'database.db'} ไปยัง {DATABASE_PATH}")
        shutil.copy(temp_dir / "database.db", DATABASE_PATH)
        print("  [SUCCESS] กู้คืนไฟล์ฐานข้อมูลสำเร็จ!")
        
        # กู้คืนรูปภาพสินค้า
        img_restore_dir = temp_dir / "products_img"
        if img_restore_dir.exists():
            dest_img_dir = PRODUCTS_IMG_DIR
            dest_img_dir.mkdir(parents=True, exist_ok=True)
            for img_file in img_restore_dir.iterdir():
                shutil.copy(img_file, dest_img_dir / img_file.name)
            print("  [SUCCESS] กู้คืนรูปภาพสินค้าสำเร็จ!")
            
        # กู้คืนใบเสร็จ
        receipt_restore_dir = temp_dir / "receipts"
        if receipt_restore_dir.exists():
            dest_receipt_dir = Path("data/receipts")
            dest_receipt_dir.mkdir(parents=True, exist_ok=True)
            for receipt_file in receipt_restore_dir.iterdir():
                shutil.copy(receipt_file, dest_receipt_dir / receipt_file.name)
            print("  [SUCCESS] กู้คืนใบเสร็จสำเร็จ!")
            
        # ลบโฟลเดอร์ temp
        shutil.rmtree(temp_dir)
        print("  [SUCCESS] ล้างข้อมูลโฟลเดอร์ชั่วคราวเสร็จสิ้น!")
        print("\n=> ผลลัพธ์: การทดสอบกู้คืนข้อมูลสำเร็จ 100% ปราศจากข้อผิดพลาด!")
        
    except Exception as e:
        print(f"\n  [CRITICAL ERROR] การกู้คืนข้อมูลเกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    run_test()
