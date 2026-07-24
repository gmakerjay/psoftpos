# -*- coding: utf-8 -*-
"""
สคริปต์สำหรับ Build โปรแกรมด้วย PyInstaller และ Deploy ไปยัง STDeploy บน Desktop
โครงสร้างโฟลเดอร์ใน C:\\Users\\admin\\Desktop\\STDeploy:
├── StorePOS_Full/           ← โปรแกรมตัวเต็ม (StorePOS.exe + data + dependencies)
├── StorePOS_30DayTrial/     ← โปรแกรมตัวทดลอง 30 วัน (StorePOS_30DayTrial.exe + data + dependencies)
└── Tools/                   ← เครื่องมือแอดมิน/ผู้ขาย (KeyGen.exe + standalone scripts)
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

# Force stdout/stderr encoding to UTF-8 to prevent Windows CP874 charmap errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Versioning Rule: Always use version 1.0.0 unless user explicitly changes it
BASE_DIR = Path(__file__).resolve().parent.parent
VERSION = "1.0.0"
TARGET_DEPLOY_DIR = Path(r"C:\Users\admin\Desktop") / f"StorePOS_v{VERSION}"
ALT_DEPLOY_DIR = Path(r"C:\Users\admin\Desktop\STDeploy")

SPEC_FULL = BASE_DIR / "tools" / "build_exe.spec"
SPEC_TRIAL30 = BASE_DIR / "tools" / "build_exe_trial_30days.spec"
SPEC_KEYGEN = BASE_DIR / "tools" / "build_keygen.spec"

DIST_FULL = BASE_DIR / "dist" / "StorePOS"
DIST_TRIAL30 = BASE_DIR / "dist" / "StorePOS_30DayTrial"
DIST_KEYGEN = BASE_DIR / "dist" / "KeyGen"

def kill_running_processes():
    """ตรวจสอบและสั่งปิด Process เพื่อป้องกันปัญหา File Lock บน Windows"""
    print("[1/6] Checking and terminating old processes...")
    target_processes = ["StorePOS.exe", "StorePOS_30DayTrial.exe", "StorePOS_3DayTrial.exe", "KeyGen.exe"]
    for proc in target_processes:
        try:
            cmd = f'taskkill /F /IM "{proc}" /T'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if "SUCCESS" in res.stdout or "สำเร็จ" in res.stdout:
                print(f"  - Terminated running process: {proc}")
        except Exception as e:
            print(f"  - Notice killing process {proc}: {e}")
    time.sleep(1)

def run_pyinstaller_builds():
    """สั่ง Build StorePOS Full และ KeyGen ด้วย PyInstaller"""
    print(f"[2/6] Building Full Application ({SPEC_FULL.name})...")
    res_full = subprocess.run([sys.executable, "-m", "PyInstaller", str(SPEC_FULL), "--clean", "--noconfirm"], cwd=str(BASE_DIR), capture_output=True, text=True)
    if res_full.returncode != 0:
        print(f"[ERROR] Full App Build Failed!\nSTDOUT:\n{res_full.stdout}\nSTDERR:\n{res_full.stderr}")
        sys.exit(1)
    print("  [SUCCESS] StorePOS Full Build Completed Successfully!")

    print(f"[4/6] Building Admin Tool KeyGen ({SPEC_KEYGEN.name})...")
    res_kg = subprocess.run([sys.executable, "-m", "PyInstaller", str(SPEC_KEYGEN), "--clean", "--noconfirm"], cwd=str(BASE_DIR), capture_output=True, text=True)
    if res_kg.returncode != 0:
        print(f"[ERROR] KeyGen Build Failed!\nSTDOUT:\n{res_kg.stdout}\nSTDERR:\n{res_kg.stderr}")
        sys.exit(1)
    print("  [SUCCESS] KeyGen Build Completed Successfully!")

def prepare_and_clear_deploy_dir():
    """เคลียร์โฟลเดอร์ปลายทาง STDeploy และ StorePOS_v1.0.0"""
    for d in [TARGET_DEPLOY_DIR, ALT_DEPLOY_DIR]:
        print(f"[5/6] Clearing target deploy directory ({d})...")
        if d.exists():
            for item in d.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    print(f"  - Retrying force delete for {item.name}: {e}")
                    time.sleep(0.5)
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        try:
                            item.unlink()
                        except Exception:
                            pass
        else:
            d.mkdir(parents=True, exist_ok=True)
        print(f"  [SUCCESS] Target deploy directory cleared: {d}")

def deploy_package(src_dist_dir, dest_package_dir):
    """คัดลอกไฟล์ Build และสร้างโครงสร้างโฟลเดอร์ประกอบสำหรับแต่ละแพ็คเกจ"""
    dest_package_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dist_dir.iterdir():
        dest = dest_package_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    (dest_package_dir / "Backup").mkdir(exist_ok=True)
    (dest_package_dir / "Logs").mkdir(exist_ok=True)
    (dest_package_dir / "Excel_Exports").mkdir(exist_ok=True)
    (dest_package_dir / "data").mkdir(exist_ok=True)

    # คัดลอกฐานข้อมูลและโฟลเดอร์รูปภาพสินค้าแบบสมบูรณ์
    src_db = BASE_DIR / "data" / "database.db"
    if src_db.exists():
        dest_db = dest_package_dir / "data" / "database.db"
        shutil.copy2(src_db, dest_db)
        
        # ล้างคีย์ทดลองเก่าออกถ้ามี
        try:
            import sqlite3
            conn = sqlite3.connect(str(dest_db))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE setting_key IN ('trial_start_date_30days', 'last_run_timestamp_30days', 'trial_start_date', 'last_run_timestamp')")
            conn.commit()
            conn.close()
        except Exception:
            pass

    # คัดลอกโฟลเดอร์รูปภาพสินค้าทั้งหมด (products, products_img, receipts)
    for img_dir_name in ["products", "products_img", "receipts"]:
        src_img_dir = BASE_DIR / "data" / img_dir_name
        if src_img_dir.exists():
            dest_img_dir = dest_package_dir / "data" / img_dir_name
            dest_img_dir.mkdir(parents=True, exist_ok=True)
            for img_file in src_img_dir.iterdir():
                if img_file.is_file():
                    try:
                        shutil.copy2(img_file, dest_img_dir / img_file.name)
                    except Exception as e_copy:
                        print(f"  - Warning copying {img_file.name}: {e_copy}")

def deploy_all_packages():
    """คัดลอกไฟล์ Build ทั้งหมดไปยังทั้ง StorePOS_v1.0.0 และ STDeploy"""
    for target in [TARGET_DEPLOY_DIR, ALT_DEPLOY_DIR]:
        print(f"[6/6] Deploying all packages to {target}...")
        
        # 1. Deploy StorePOS_Full
        dest_full = target / "StorePOS_Full"
        print(f"  - Deploying Full version to {dest_full.name}...")
        deploy_package(DIST_FULL, dest_full)

        # 2. Deploy Tools
        dest_tools = target / "Tools"
        dest_tools.mkdir(parents=True, exist_ok=True)
        print(f"  - Deploying KeyGen compiled executable to {dest_tools.name}...")
        if DIST_KEYGEN.exists():
            for item in DIST_KEYGEN.iterdir():
                dest_item = dest_tools / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)

        # คัดลอกไฟล์สคริปต์แอดมินเพิ่มเติมลงใน Tools
        admin_scripts = [
            BASE_DIR / "keygen_standalone.py",
            BASE_DIR / "tools" / "keygen_standalone.py",
            BASE_DIR / "tools" / "license_generator.py",
            BASE_DIR / "tools" / "license_manager.py"
        ]
        for script_path in admin_scripts:
            if script_path.exists():
                shutil.copy2(script_path, dest_tools / script_path.name)
                print(f"  - Copied admin script: {script_path.name} to Tools")

    print("  [SUCCESS] All packages deployed to StorePOS_v1.0.0 & STDeploy successfully!")

def verify_deployment():
    """ตรวจสอบความถูกต้องของการ Deploy ทั้ง 3 ส่วน"""
    print(f"Verifying deployed packages at {TARGET_DEPLOY_DIR}...")
    exe_full = TARGET_DEPLOY_DIR / "StorePOS_Full" / "StorePOS.exe"
    exe_trial = TARGET_DEPLOY_DIR / "StorePOS_30DayTrial" / "StorePOS_30DayTrial.exe"
    exe_keygen = TARGET_DEPLOY_DIR / "Tools" / "KeyGen.exe"
    py_keygen = TARGET_DEPLOY_DIR / "Tools" / "keygen_standalone.py"

    if exe_full.exists():
        size_mb = exe_full.stat().st_size / (1024 * 1024)
        print(f"  [SUCCESS] StorePOS_Full/StorePOS.exe verified! Size: {size_mb:.2f} MB")
    else:
        print("[WARNING] Verification warning: StorePOS_Full/StorePOS.exe not found!")

    # 30-Day Trial verification skipped per user preference
    # if exe_trial.exists():
    #     tr_mb = exe_trial.stat().st_size / (1024 * 1024)
    #     print(f"  [SUCCESS] StorePOS_30DayTrial/StorePOS_30DayTrial.exe verified! Size: {tr_mb:.2f} MB")
    # else:
    #     print("[WARNING] Verification warning: StorePOS_30DayTrial/StorePOS_30DayTrial.exe not found!")

    if exe_keygen.exists():
        kg_mb = exe_keygen.stat().st_size / (1024 * 1024)
        print(f"  [SUCCESS] Tools/KeyGen.exe verified! Size: {kg_mb:.2f} MB")
    else:
        print("[WARNING] Verification warning: Tools/KeyGen.exe not found!")

    if py_keygen.exists():
        print(f"  [SUCCESS] Tools/keygen_standalone.py verified!")

if __name__ == "__main__":
    print("==================================================")
    print("      StorePOS Full, Trial & Tools Deploy Script  ")
    print("==================================================")
    kill_running_processes()
    run_pyinstaller_builds()
    prepare_and_clear_deploy_dir()
    deploy_all_packages()
    verify_deployment()
    print("==================================================")
    print("      ALL BUILD & DEPLOY STEPS COMPLETED!         ")
    print("==================================================")
