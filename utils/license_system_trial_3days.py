# -*- coding: utf-8 -*-
"""
Hardware ID & License System - 3-Day Trial Version
ระบบตรวจสอบการทดลองใช้งาน 3 วัน โดยใช้วิธีเก็บรักษาวันที่เริ่มใช้อย่างปลอดภัย
"""

import uuid
import hashlib
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
import base64
from tkinter import messagebox
from database.db_manager import DatabaseManager
from utils.logger import log_error, log_info

class HardwareID:
    """จัดการ Hardware ID"""
    
    @staticmethod
    def get_motherboard_uuid():
        try:
            if platform.system() == "Windows":
                try:
                    cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"]
                    result = subprocess.check_output(cmd, creationflags=0x08000000).decode().strip()
                    if result and result.lower() != "to be filled by o.e.m.":
                        return result
                except:
                    pass
                try:
                    cmd = "wmic csproduct get uuid"
                    result = subprocess.check_output(cmd, shell=True).decode()
                    uuid_line = result.split('\n')[1].strip()
                    if uuid_line and uuid_line.lower() != "to be filled by o.e.m.":
                        return uuid_line
                except:
                    pass
            return "UNKNOWN_MB_UUID"
        except:
            return "UNKNOWN_MB_UUID"
            
    @staticmethod
    def get_cpu_id():
        try:
            if platform.system() == "Windows":
                try:
                    cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty ProcessorId"]
                    result = subprocess.check_output(cmd, creationflags=0x08000000).decode().strip()
                    if result:
                        return result
                except:
                    pass
                try:
                    cmd = "wmic cpu get processorid"
                    result = subprocess.check_output(cmd, shell=True).decode()
                    cpu_id = result.split('\n')[1].strip()
                    if cpu_id:
                        return cpu_id
                except:
                    pass
            return "UNKNOWN_CPU"
        except:
            return "UNKNOWN_CPU"

    @staticmethod
    def get_disk_serial():
        try:
            if platform.system() == "Windows":
                import ctypes
                volumeNameBuffer = ctypes.create_unicode_buffer(1024)
                fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
                serial_number = ctypes.c_ulong(0)
                max_component_length = ctypes.c_ulong(0)
                file_system_flags = ctypes.c_ulong(0)
                
                rc = ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p("C:\\"),
                    volumeNameBuffer,
                    ctypes.sizeof(volumeNameBuffer),
                    ctypes.byref(serial_number),
                    ctypes.byref(max_component_length),
                    ctypes.byref(file_system_flags),
                    fileSystemNameBuffer,
                    ctypes.sizeof(fileSystemNameBuffer)
                )
                if rc:
                    return f"{serial_number.value:08X}"
            return "UNKNOWN_DISK"
        except:
            return "UNKNOWN_DISK"

    @staticmethod
    def get_machine_guid():
        try:
            if platform.system() == "Windows":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
                return str(value).strip()
            return "UNKNOWN_GUID"
        except:
            return "UNKNOWN_GUID"

    @staticmethod
    def generate_hwid():
        mb = HardwareID.get_motherboard_uuid()
        cpu = HardwareID.get_cpu_id()
        disk = HardwareID.get_disk_serial()
        guid = HardwareID.get_machine_guid()
        
        fallback = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:8].upper()
        
        mb_h = hashlib.sha256(mb.encode()).hexdigest()[:8].upper() if mb != "UNKNOWN_MB_UUID" else fallback
        cpu_h = hashlib.sha256(cpu.encode()).hexdigest()[:8].upper() if cpu != "UNKNOWN_CPU" else fallback
        disk_h = hashlib.sha256(disk.encode()).hexdigest()[:8].upper() if disk != "UNKNOWN_DISK" else fallback
        guid_h = hashlib.sha256(guid.encode()).hexdigest()[:8].upper() if guid != "UNKNOWN_GUID" else fallback
        
        return f"{mb_h}-{cpu_h}-{disk_h}-{guid_h}"


class LicenseManager:
    """จัดการสิทธิ์การใช้งานสำหรับเวอร์ชันทดลอง 3 วัน"""
    
    TRIAL_FILE = Path("data/.trial_3days")
    LICENSE_FILE = Path("data/.license_3days")
    MANUAL_LICENSE_PATH = None
    
    @staticmethod
    def set_manual_license_path(path):
        pass

    @staticmethod
    def get_license_file_path(write_mode=False):
        return LicenseManager.LICENSE_FILE

    @staticmethod
    def log_license_action(action, license_key=None, hwid=None, details=""):
        try:
            db = DatabaseManager()
            db.connect()
            db.execute("""
                INSERT INTO license_logs (action, license_key, hwid, details)
                VALUES (?, ?, ?, ?)
            """, (action, license_key, hwid, details))
            db.disconnect()
        except Exception as e:
            print(f"Error logging license action: {e}")

    @staticmethod
    def check_hwid_match(current_hwid, registered_hwid):
        return True

    @staticmethod
    def generate_license_key(hwid, expire_days=3, features=None):
        return "TRIAL-VERSION-3-DAYS-FREE"
    
    @staticmethod
    def validate_license_key(license_key, current_hwid):
        is_val, msg, data = LicenseManager.check_activation()
        return is_val, msg, data
    
    @staticmethod
    def get_expiry_warning(license_data):
        """แจ้งเตือนวันหมดอายุสำหรับตัวทดลองใช้งาน"""
        try:
            days_left = license_data.get('days_left', 0)
            expire_date_str = license_data.get('expire_date', '')
            total_days = 3
            license_type = "ทดลองใช้ฟรี (3 วัน)"
            
            if days_left <= 0:
                return {
                    'level': 'expired',
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': '⛔ เวอร์ชันทดลองหมดอายุแล้ว!',
                    'message': (
                        f"ระยะเวลาทดลองใช้งานฟรี 3 วันหมดลงแล้ว!\n\n"
                        f"📅 วันหมดอายุ: {expire_date_str}\n\n"
                        f"❌ โปรแกรมหยุดทำงาน กรุณาติดต่อผู้ขายเพื่อสั่งซื้อสิทธิ์การใช้งานจริง"
                    )
                }
            elif days_left <= 1:
                level = 'critical'
                days_text = "วันนี้เป็นวันสุดท้าย!" if days_left == 0 else f"เหลืออีก {days_left} วัน"
                return {
                    'level': level,
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': f'⚠️ เวอร์ชันทดลองใกล้หมดเวลา! ({days_text})',
                    'message': (
                        f"⏰ ระยะเวลาทดลองใช้งานฟรีใกล้หมดลงแล้ว!\n\n"
                        f"📅 วันหมดอายุ: {expire_date_str}\n"
                        f"⏳ {days_text}\n\n"
                        f"⚠️ กรุณาติดต่อซื้อสิทธิ์การใช้งานเพื่อใช้งานระบบต่อได้อย่างต่อเนื่อง"
                    )
                }
            else:
                return {
                    'level': 'none',
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': '',
                    'message': ''
                }
        except Exception:
            return {
                'level': 'none',
                'days_left': -1,
                'expire_date': '',
                'total_days': 0,
                'license_type': '',
                'title': '',
                'message': ''
            }
    
    @staticmethod
    def save_license(license_key):
        messagebox.showinfo("ทดลองใช้งาน", "โปรแกรมนี้เป็นเวอร์ชันทดลองใช้ฟรี 3 วัน ไม่จำเป็นต้องระบุคีย์สิทธิ์การใช้งาน")
        return True
    
    @staticmethod
    def load_license():
        return "TRIAL-VERSION-3-DAYS-FREE"
    
    @staticmethod
    def delete_license():
        messagebox.showwarning("ทดลองใช้งาน", "ไม่สามารถถอดถอนสิทธิ์ในเวอร์ชันทดลองใช้ฟรี 3 วันได้")
        return False
            
    @staticmethod
    def transfer_license():
        messagebox.showwarning("ทดลองใช้งาน", "ไม่สามารถโอนย้ายสิทธิ์ในเวอร์ชันทดลองใช้ฟรี 3 วันได้")
        return False, "เวอร์ชันทดลองไม่สนับสนุนการโอนย้ายสิทธิ์", None

    @staticmethod
    def verify_system_clock():
        """ตรวจสอบการย้อนเวลาเพื่อโกงสิทธิ์ตัวทดลอง"""
        try:
            db = DatabaseManager()
            db.connect()
            
            result = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'last_run_timestamp_3days'")
            current_time = datetime.now()
            
            if result:
                last_time_str = result['setting_value']
                try:
                    last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                except:
                    last_time = None
                    
                if last_time and current_time < last_time:
                    db.disconnect()
                    return False, f"ตรวจพบการย้อนเวลาเครื่อง! (เวลาปัจจุบัน: {current_time.strftime('%Y-%m-%d %H:%M:%S')}, เวลาการใช้งานล่าสุด: {last_time_str})"
            
            db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp_3days', ?)", 
                       (current_time.strftime("%Y-%m-%d %H:%M:%S"),))
            db.disconnect()
            return True, ""
        except Exception as e:
            log_error(f"Error checking system clock in 3-day trial: {e}")
            return True, str(e)

    @staticmethod
    def _read_trial_file():
        """อ่านวันเริ่มต้นจากไฟล์ลับ"""
        try:
            if not LicenseManager.TRIAL_FILE.exists():
                return None
            with open(LicenseManager.TRIAL_FILE, 'r') as f:
                content = f.read().strip()
            decoded = base64.b64decode(content.encode()).decode()
            return datetime.strptime(decoded, "%Y-%m-%d %H:%M:%S")
        except:
            return None

    @staticmethod
    def _write_trial_file(dt):
        """เขียนวันเริ่มต้นลงไฟล์ลับ"""
        try:
            LicenseManager.TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            encoded = base64.b64encode(dt_str.encode()).decode()
            with open(LicenseManager.TRIAL_FILE, 'w') as f:
                f.write(encoded)
            return True
        except Exception as e:
            log_error(f"Error writing 3-day trial file: {e}")
            return False

    @staticmethod
    def _get_trial_db_date():
        """อ่านวันเริ่มต้นจากฐานข้อมูล"""
        try:
            db = DatabaseManager()
            db.connect()
            result = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'trial_start_date_3days'")
            db.disconnect()
            if result:
                decoded = base64.b64decode(result['setting_value'].encode()).decode()
                return datetime.strptime(decoded, "%Y-%m-%d %H:%M:%S")
            return None
        except Exception as e:
            log_error(f"Error getting 3-day trial DB date: {e}")
            return None

    @staticmethod
    def _write_trial_db_date(dt):
        """บันทึกวันเริ่มต้นลงฐานข้อมูล"""
        try:
            db = DatabaseManager()
            db.connect()
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            encoded = base64.b64encode(dt_str.encode()).decode()
            db.execute("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value)
                VALUES ('trial_start_date_3days', ?)
            """, (encoded,))
            db.disconnect()
            return True
        except Exception as e:
            log_error(f"Error writing 3-day trial DB date: {e}")
            return False

    @staticmethod
    def check_activation():
        """ตรวจสอบเวลาทดลองใช้ 3 วัน"""
        clock_ok, clock_msg = LicenseManager.verify_system_clock()
        if not clock_ok:
            return False, clock_msg, None
            
        current_time = datetime.now()
        
        file_date = LicenseManager._read_trial_file()
        db_date = LicenseManager._get_trial_db_date()
        
        trial_start = None
        
        if file_date and db_date:
            if file_date < db_date:
                trial_start = file_date
                LicenseManager._write_trial_db_date(file_date)
            else:
                trial_start = db_date
                LicenseManager._write_trial_file(db_date)
        elif file_date:
            trial_start = file_date
            LicenseManager._write_trial_db_date(file_date)
        elif db_date:
            trial_start = db_date
            LicenseManager._write_trial_file(db_date)
        else:
            trial_start = current_time
            LicenseManager._write_trial_file(current_time)
            LicenseManager._write_trial_db_date(current_time)
            
        if current_time < trial_start:
            return False, f"ตรวจพบการโกงเวลาเครื่อง! เวลาปัจจุบันก่อนวันเริ่มทดลองใช้งาน (เริ่มทดลอง: {trial_start.strftime('%Y-%m-%d %H:%M:%S')})", None
            
        days_used = (current_time - trial_start).days
        days_left = max(0, 3 - days_used)
        
        expire_date = trial_start + timedelta(days=3)
        expire_date_str = expire_date.strftime("%Y-%m-%d")
        
        features = {
            "pos": True,
            "inventory": True,
            "reports": True,
            "multi_user": True,
            "customer_display": True,
            "thermal_printer": True,
            "barcode_scanner": True,
            "tax_invoice": True,
            "delivery_note": True
        }
        
        license_data = {
            "hwid": HardwareID.generate_hwid(),
            "expire_date": expire_date_str,
            "features": features,
            "issued_date": trial_start.strftime("%Y-%m-%d %H:%M:%S"),
            "is_trial": True,
            "days_left": days_left
        }
        
        if days_used >= 3:
            return False, f"เวอร์ชันทดลองใช้ฟรีหมดอายุแล้วเมื่อ {expire_date_str}", license_data
            
        return True, f"เวอร์ชันทดลองใช้งานคงเหลือ {days_left} วัน (หมดอายุ: {expire_date_str})", license_data

if __name__ == "__main__":
    is_ok, msg, data = LicenseManager.check_activation()
    print(f"3-Day Trial OK? {is_ok}")
    print(f"Message: {msg}")
    print(f"Data: {data}")
