# -*- coding: utf-8 -*-
"""
Hardware ID & License System
ระบบตรวจสอบ Hardware ID และ License Key
"""

import uuid
import hashlib
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
import base64


class HardwareID:
    """จัดการ Hardware ID"""
    
    @staticmethod
    def get_machine_id():
        """ดึง Machine ID จากระบบ"""
        try:
            if platform.system() == "Windows":
                # ใช้ WMIC เพื่อดึง UUID ของ Motherboard
                cmd = "wmic csproduct get uuid"
                result = subprocess.check_output(cmd, shell=True).decode()
                uuid_line = result.split('\n')[1].strip()
                return uuid_line
            else:
                # Linux/Mac
                return str(uuid.getnode())
        except:
            # Fallback: ใช้ MAC Address
            return str(uuid.getnode())
    
    @staticmethod
    def get_motherboard_serial():
        """ดึง Serial Number ของ Motherboard"""
        try:
            if platform.system() == "Windows":
                cmd = "wmic baseboard get serialnumber"
                result = subprocess.check_output(cmd, shell=True).decode()
                serial = result.split('\n')[1].strip()
                return serial
            return "UNKNOWN"
        except:
            return "UNKNOWN"
    
    @staticmethod
    def get_cpu_id():
        """ดึง CPU ID"""
        try:
            if platform.system() == "Windows":
                cmd = "wmic cpu get processorid"
                result = subprocess.check_output(cmd, shell=True).decode()
                cpu_id = result.split('\n')[1].strip()
                return cpu_id
            return "UNKNOWN"
        except:
            return "UNKNOWN"
    
    @staticmethod
    def generate_hwid():
        """สร้าง HWID ที่ไม่ซ้ำสำหรับเครื่องนี้"""
        machine_id = HardwareID.get_machine_id()
        mb_serial = HardwareID.get_motherboard_serial()
        cpu_id = HardwareID.get_cpu_id()
        
        # รวม Hardware Info
        hw_string = f"{machine_id}|{mb_serial}|{cpu_id}"
        
        # Hash เป็น SHA256
        hwid = hashlib.sha256(hw_string.encode()).hexdigest()
        
        # ตัดให้เหลือ 32 ตัวอักษร แบ่งเป็น 4 กลุ่ม
        hwid_formatted = f"{hwid[:8]}-{hwid[8:16]}-{hwid[16:24]}-{hwid[24:32]}".upper()
        
        return hwid_formatted


class LicenseManager:
    """จัดการ License Key"""
    
    LICENSE_FILE = Path("data/.license")
    SECRET_KEY = b"POS_SYSTEM_2026_SECRET_KEY_DO_NOT_SHARE"  # ต้องเปลี่ยนเป็นของจริง
    
    @staticmethod
    def generate_license_key(hwid, expire_days=365, features=None):
        """
        สร้าง License Key สำหรับ HWID นี้
        
        Args:
            hwid: Hardware ID
            expire_days: จำนวนวันที่ใช้งานได้
            features: dict ของฟีเจอร์ที่เปิดใช้งาน
        """
        if features is None:
            features = {
                "pos": True,
                "inventory": True,
                "reports": True,
                "multi_user": True,
                "customer_display": True,
                "thermal_printer": True
            }
        
        expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d")
        
        # สร้าง License Data
        license_data = {
            "hwid": hwid,
            "expire_date": expire_date,
            "features": features,
            "issued_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # แปลงเป็น JSON
        json_data = json.dumps(license_data, sort_keys=True)
        
        # เข้ารหัสด้วย Base64
        encoded = base64.b64encode(json_data.encode()).decode()
        
        # สร้าง Signature
        signature = hashlib.sha256(
            (encoded + hwid + LicenseManager.SECRET_KEY.decode()).encode()
        ).hexdigest()[:16]
        
        # รวม License Key: SIGNATURE-ENCODED_DATA
        license_key = f"{signature.upper()}-{encoded}"
        
        return license_key
    
    @staticmethod
    def validate_license_key(license_key, hwid):
        """
        ตรวจสอบ License Key ว่าถูกต้องและตรงกับ HWID นี้หรือไม่
        
        Returns:
            tuple: (is_valid, message, license_data)
        """
        try:
            # แยก Signature และ Data
            parts = license_key.split('-', 1)
            if len(parts) != 2:
                return False, "รูปแบบ License Key ไม่ถูกต้อง", None
            
            signature, encoded_data = parts
            
            # ตรวจสอบ Signature
            expected_sig = hashlib.sha256(
                (encoded_data + hwid + LicenseManager.SECRET_KEY.decode()).encode()
            ).hexdigest()[:16].upper()
            
            if signature != expected_sig:
                return False, "License Key ไม่ถูกต้อง (Signature ไม่ตรง)", None
            
            # Decode Data
            json_data = base64.b64decode(encoded_data.encode()).decode()
            license_data = json.loads(json_data)
            
            # ตรวจสอบ HWID
            if license_data['hwid'] != hwid:
                return False, "License Key นี้ไม่ตรงกับเครื่องนี้", None
            
            # ตรวจสอบวันหมดอายุ
            expire_date = datetime.strptime(license_data['expire_date'], "%Y-%m-%d")
            if datetime.now() > expire_date:
                return False, f"License หมดอายุแล้ว (หมดอายุ: {license_data['expire_date']})", None
            
            days_left = (expire_date - datetime.now()).days
            
            return True, f"License ถูกต้อง (เหลืออีก {days_left} วัน)", license_data
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}", None
    
    @staticmethod
    def save_license(license_key):
        """บันทึก License Key ลงไฟล์"""
        try:
            LicenseManager.LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # เข้ารหัสก่อนบันทึก (Obfuscation เบื้องต้น)
            encrypted = base64.b64encode(license_key.encode()).decode()
            
            with open(LicenseManager.LICENSE_FILE, 'w') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"Error saving license: {e}")
            return False
    
    @staticmethod
    def load_license():
        """โหลด License Key จากไฟล์"""
        try:
            if not LicenseManager.LICENSE_FILE.exists():
                return None
            
            with open(LicenseManager.LICENSE_FILE, 'r') as f:
                encrypted = f.read()
            
            # ถอดรหัส
            license_key = base64.b64decode(encrypted.encode()).decode()
            
            return license_key
        except:
            return None
    
    @staticmethod
    def delete_license():
        """ลบ License Key"""
        try:
            if LicenseManager.LICENSE_FILE.exists():
                LicenseManager.LICENSE_FILE.unlink()
            return True
        except:
            return False
    
    @staticmethod
    def check_activation():
        """
        ตรวจสอบว่าโปรแกรมถูก Activate แล้วหรือไม่
        
        Returns:
            tuple: (is_activated, message, license_data)
        """
        # โหลด License
        license_key = LicenseManager.load_license()
        
        if not license_key:
            return False, "ไม่พบ License Key - กรุณา Activate โปรแกรม", None
        
        # ดึง HWID
        hwid = HardwareID.generate_hwid()
        
        # ตรวจสอบ License
        return LicenseManager.validate_license_key(license_key, hwid)


# ทดสอบ
if __name__ == "__main__":
    print("="*60)
    print("Hardware ID & License System")
    print("="*60)
    
    # แสดง Hardware Info
    print("\n[Hardware Information]")
    print(f"Machine ID: {HardwareID.get_machine_id()}")
    print(f"Motherboard Serial: {HardwareID.get_motherboard_serial()}")
    print(f"CPU ID: {HardwareID.get_cpu_id()}")
    
    # สร้าง HWID
    hwid = HardwareID.generate_hwid()
    print(f"\n[Your HWID]")
    print(f"{hwid}")
    print("\n✅ ส่ง HWID นี้ให้ผู้ขายเพื่อรับ License Key")
    
    # ทดสอบสร้าง License (ฝั่งผู้ขาย)
    print("\n" + "="*60)
    print("[Testing License Generation]")
    license_key = LicenseManager.generate_license_key(hwid, expire_days=365)
    print(f"\nLicense Key:\n{license_key}")
    
    # ทดสอบตรวจสอบ License
    print("\n" + "="*60)
    print("[Testing License Validation]")
    is_valid, message, data = LicenseManager.validate_license_key(license_key, hwid)
    print(f"Valid: {is_valid}")
    print(f"Message: {message}")
    if data:
        print(f"Expire Date: {data['expire_date']}")
        print(f"Features: {data['features']}")
