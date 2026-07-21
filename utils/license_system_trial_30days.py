# -*- coding: utf-8 -*-
"""
Hardware ID & License System - 30-Day Trial Version (1 เดือน)
ระบบตรวจสอบการทดลองใช้งาน 30 วัน โดยใช้วิธีเก็บรักษาวันที่เริ่มใช้อย่างปลอดภัย

ป้องกันการลักลอบใช้:
  - เก็บ trial start date ใน 3 แหล่ง: ไฟล์ / ฐานข้อมูล / Windows Registry
  - แม้ลบโปรแกรมแล้วลงใหม่ Registry ยังคงอยู่ → ใช้ซ้ำไม่ได้
  - ตรวจสอบการย้อนเวลาเครื่อง
  - Hardware ID ผูกกับเครื่อง

ข้อมูลลูกค้า:
  - DB ยังคงอยู่แม้หมดอายุ → ลูกค้าซื้อจริงแล้วนำข้อมูลกลับมาใช้ได้
  - ระบบ Backup ยังทำงานได้ปกติแม้หมดอายุ
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

# === Registry Key สำหรับป้องกันการลบลงใหม่ ===
REGISTRY_KEY_PATH = r"SOFTWARE\PSoftPOS"
REGISTRY_VALUE_NAME = "TrialData30"
REGISTRY_HWID_NAME = "DeviceFingerprint30"


class HardwareID:
    """จัดการ Hardware ID"""
    
    @staticmethod
    def get_motherboard_uuid():
        try:
            if platform.system() == "Windows":
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
                    vendor, _ = winreg.QueryValueEx(key, "SystemManufacturer")
                    prod, _ = winreg.QueryValueEx(key, "SystemProductName")
                    board, _ = winreg.QueryValueEx(key, "BaseBoardProduct")
                    winreg.CloseKey(key)
                    mb_str = f"{vendor}-{prod}-{board}".strip()
                    if mb_str and mb_str.lower() != "to be filled by o.e.m.":
                        return mb_str
                except:
                    pass
            return "UNKNOWN_MB_UUID"
        except:
            return "UNKNOWN_MB_UUID"
            
    @staticmethod
    def get_cpu_id():
        try:
            if platform.system() == "Windows":
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    proc_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    proc_id, _ = winreg.QueryValueEx(key, "Identifier")
                    winreg.CloseKey(key)
                    cpu_str = f"{proc_name}-{proc_id}".strip()
                    if cpu_str:
                        return cpu_str
                except:
                    pass
                proc_env = os.environ.get('PROCESSOR_IDENTIFIER')
                if proc_env:
                    return proc_env
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

    _cached_hwid = None

    @staticmethod
    def generate_hwid():
        if HardwareID._cached_hwid is not None:
            return HardwareID._cached_hwid

        mb = HardwareID.get_motherboard_uuid()
        cpu = HardwareID.get_cpu_id()
        disk = HardwareID.get_disk_serial()
        guid = HardwareID.get_machine_guid()
        
        fallback = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:8].upper()
        
        mb_h = hashlib.sha256(mb.encode()).hexdigest()[:8].upper() if mb != "UNKNOWN_MB_UUID" else fallback
        cpu_h = hashlib.sha256(cpu.encode()).hexdigest()[:8].upper() if cpu != "UNKNOWN_CPU" else fallback
        disk_h = hashlib.sha256(disk.encode()).hexdigest()[:8].upper() if disk != "UNKNOWN_DISK" else fallback
        guid_h = hashlib.sha256(guid.encode()).hexdigest()[:8].upper() if guid != "UNKNOWN_GUID" else fallback
        
        HardwareID._cached_hwid = f"{mb_h}-{cpu_h}-{disk_h}-{guid_h}"
        return HardwareID._cached_hwid



class LicenseManager:
    """จัดการสิทธิ์การใช้งานสำหรับเวอร์ชันทดลอง 30 วัน (1 เดือน)
    
    ป้องกันการลักลอบใช้:
    - เก็บ trial start date ใน 3 แหล่ง (file / DB / Windows Registry)
    - แม้ลบโปรแกรมแล้วลงใหม่ → Registry ยังอยู่ → ใช้ซ้ำไม่ได้
    - ตรวจสอบการย้อนเวลาเครื่อง
    - ผูก Hardware ID กับเครื่อง
    
    ข้อมูลลูกค้า:
    - DB ยังคงอยู่แม้หมดอายุ
    - Backup ยังทำได้ปกติ
    """
    
    TRIAL_DAYS = 30
    TRIAL_FILE = Path("data/.trial_30days")
    LICENSE_FILE = Path("data/.license_30days")
    MANUAL_LICENSE_PATH = None
    
    SECRET_KEY = b"POS_SYSTEM_2026_SECRET_KEY_DO_NOT_SHARE"

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
        curr_parts = current_hwid.split("-")
        targ_parts = registered_hwid.split("-")
        if len(curr_parts) != 4 or len(targ_parts) != 4:
            return False
        matches = sum(1 for c, t in zip(curr_parts, targ_parts) if c == t)
        return matches >= 3

    @staticmethod
    def generate_license_key(hwid, expire_days=365, features=None):
        if features is None:
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
        expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d")
        license_data = {
            "hwid": hwid,
            "expire_date": expire_date,
            "features": features,
            "issued_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        json_data = json.dumps(license_data, sort_keys=True)
        encoded = base64.b64encode(json_data.encode()).decode()
        signature = hashlib.sha256(
            (encoded + hwid + LicenseManager.SECRET_KEY.decode()).encode()
        ).hexdigest()[:16]
        return f"{signature.upper()}-{encoded}"
    
    @staticmethod
    def validate_license_key(license_key, current_hwid):
        """ตรวจสอบ License Key ว่าเป็น Full License หรือไม่"""
        if not license_key or str(license_key).startswith("TRIAL-"):
            return False, "ไม่มี License Key หรือเป็นคีย์ทดลอง", None
        try:
            parts = license_key.split('-', 1)
            if len(parts) != 2:
                return False, "รูปแบบ License Key ไม่ถูกต้อง", None
            
            signature, encoded_data = parts
            json_data = base64.b64decode(encoded_data.encode()).decode()
            license_data = json.loads(json_data)
            
            registered_hwid = license_data.get('hwid', '')
            expected_sig = hashlib.sha256(
                (encoded_data + registered_hwid + LicenseManager.SECRET_KEY.decode()).encode()
            ).hexdigest()[:16].upper()
            
            if signature != expected_sig:
                return False, "License Key ไม่ถูกต้อง (Signature ไม่ตรง)", None
            
            if isinstance(registered_hwid, str):
                registered_hwids = [h.strip() for h in registered_hwid.split(',')] if ',' in registered_hwid else [registered_hwid]
            else:
                registered_hwids = []
                
            hwid_matched = any(LicenseManager.check_hwid_match(current_hwid, reg_hwid) for reg_hwid in registered_hwids)
            if not hwid_matched:
                return False, "License Key นี้ไม่ตรงกับฮาร์ดแวร์ของเครื่องนี้", None
            
            expire_date = datetime.strptime(license_data['expire_date'], "%Y-%m-%d")
            if datetime.now().date() > expire_date.date():
                return False, f"License หมดอายุแล้ว (หมดอายุ: {license_data['expire_date']})", None
            
            days_left = (expire_date.date() - datetime.now().date()).days
            license_data['days_left'] = max(0, days_left)
            license_data['is_trial'] = False
            
            return True, f"License ถูกต้อง (เหลืออีก {days_left} วัน)", license_data
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}", None

    @staticmethod
    def get_expiry_warning(license_data):
        """แจ้งเตือนวันหมดอายุสำหรับตัวทดลองใช้งาน"""
        try:
            days_left = license_data.get('days_left', 0)
            expire_date_str = license_data.get('expire_date', '')
            total_days = LicenseManager.TRIAL_DAYS
            license_type = f"ทดลองใช้ฟรี ({total_days} วัน)"
            
            if days_left <= 0:
                return {
                    'level': 'expired',
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': '⛔ เวอร์ชันทดลองหมดอายุแล้ว!',
                    'message': (
                        f"ระยะเวลาทดลองใช้งานฟรี {total_days} วันหมดลงแล้ว!\n\n"
                        f"📅 วันหมดอายุ: {expire_date_str}\n\n"
                        f"📦 ข้อมูลสินค้าและการขายของท่านยังคงอยู่ครบถ้วน\n"
                        f"สามารถนำข้อมูลกลับมาใช้ได้เมื่อซื้อเวอร์ชันเต็ม\n\n"
                        f"❌ โปรแกรมหยุดทำงาน กรุณาติดต่อผู้ขายเพื่อสั่งซื้อสิทธิ์การใช้งานจริง"
                    )
                }
            elif days_left <= 3:
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
                        f"📦 ข้อมูลทั้งหมดจะยังคงอยู่ครบถ้วนแม้หมดอายุ\n"
                        f"⚠️ กรุณาติดต่อซื้อสิทธิ์การใช้งานเพื่อใช้งานระบบต่อได้อย่างต่อเนื่อง"
                    )
                }
            elif days_left <= 7:
                level = 'warning'
                days_text = f"เหลืออีก {days_left} วัน"
                return {
                    'level': level,
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': f'ℹ️ เวอร์ชันทดลองเหลือเวลาอีก {days_left} วัน',
                    'message': (
                        f"📅 ระยะเวลาทดลองใช้งานฟรีเหลืออีก {days_left} วัน\n\n"
                        f"📅 วันหมดอายุ: {expire_date_str}\n\n"
                        f"💡 กรุณาติดต่อซื้อสิทธิ์การใช้งานก่อนหมดอายุเพื่อใช้งานต่อเนื่อง"
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
        """บันทึก Full License Key เมื่อลูกค้าลงทะเบียนสั่งซื้อ"""
        try:
            hwid = HardwareID.generate_hwid()
            is_valid, msg, license_data = LicenseManager.validate_license_key(license_key, hwid)
            if not is_valid:
                messagebox.showerror("ลงทะเบียนไม่สำเร็จ", msg)
                return False

            path = LicenseManager.LICENSE_FILE
            path.parent.mkdir(parents=True, exist_ok=True)
            encrypted = base64.b64encode(license_key.encode()).decode()
            with open(path, 'w') as f:
                f.write(encrypted)
            LicenseManager.log_license_action("ACTIVATE", license_key, hwid, "ปลดล็อกคีย์สำเร็จเปลี่ยนเป็นเวอร์ชันเต็ม")
            messagebox.showinfo("ลงทะเบียนสำเร็จ ✅", "ยินดีต้อนรับสู่ StorePOS เวอร์ชันเต็ม!\nระบบได้ทำการปลดล็อกเป็นเวอร์ชันเต็มเรียบร้อยแล้ว")
            return True
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึก License Key ได้: {e}")
            return False
    
    @staticmethod
    def load_license():
        try:
            if LicenseManager.LICENSE_FILE.exists():
                with open(LicenseManager.LICENSE_FILE, 'r') as f:
                    content = f.read().strip()
                return base64.b64decode(content.encode()).decode()
        except:
            pass
        return None
    
    @staticmethod
    def delete_license():
        try:
            if LicenseManager.LICENSE_FILE.exists():
                LicenseManager.LICENSE_FILE.unlink()
                return True
        except:
            pass
        return False
            
    @staticmethod
    def transfer_license():
        messagebox.showwarning("ทดลองใช้งาน", f"ไม่สามารถโอนย้ายสิทธิ์ในเวอร์ชันทดลองใช้ฟรี {LicenseManager.TRIAL_DAYS} วันได้")
        return False, "เวอร์ชันทดลองไม่สนับสนุนการโอนย้ายสิทธิ์", None

    # ======================================================================
    # Windows Registry — ป้องกันการลบลงใหม่
    # ======================================================================

    @staticmethod
    def _read_registry_trial_date():
        """อ่านวันเริ่มต้น trial จาก Windows Registry (HKCU)
        แม้ลบโปรแกรมแล้วลงใหม่ Registry ยังคงอยู่"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY_PATH, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, REGISTRY_VALUE_NAME)
            winreg.CloseKey(key)
            decoded = base64.b64decode(value.encode()).decode()
            return datetime.strptime(decoded, "%Y-%m-%d %H:%M:%S")
        except FileNotFoundError:
            return None
        except Exception as e:
            log_error(f"Error reading registry trial date: {e}")
            return None

    @staticmethod
    def _write_registry_trial_date(dt):
        """เขียนวันเริ่มต้น trial ลง Windows Registry (HKCU)"""
        try:
            import winreg
            # สร้าง key ถ้ายังไม่มี
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REGISTRY_KEY_PATH, 0, winreg.KEY_WRITE)
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            encoded = base64.b64encode(dt_str.encode()).decode()
            winreg.SetValueEx(key, REGISTRY_VALUE_NAME, 0, winreg.REG_SZ, encoded)
            # เก็บ HWID ด้วยเพื่อผูกกับเครื่อง
            hwid = HardwareID.generate_hwid()
            hwid_encoded = base64.b64encode(hwid.encode()).decode()
            winreg.SetValueEx(key, REGISTRY_HWID_NAME, 0, winreg.REG_SZ, hwid_encoded)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            log_error(f"Error writing registry trial date: {e}")
            return False

    @staticmethod
    def _read_registry_hwid():
        """อ่าน Hardware ID ที่ผูกไว้ใน Registry"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY_PATH, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, REGISTRY_HWID_NAME)
            winreg.CloseKey(key)
            decoded = base64.b64decode(value.encode()).decode()
            return decoded
        except FileNotFoundError:
            return None
        except Exception as e:
            log_error(f"Error reading registry HWID: {e}")
            return None

    # ======================================================================
    # ตรวจสอบเวลา
    # ======================================================================

    @staticmethod
    def verify_system_clock():
        """ตรวจสอบการย้อนเวลาเพื่อโกงสิทธิ์ตัวทดลองแบบปลอดภัยไม่บล็อกระบบ"""
        try:
            db = DatabaseManager()
            if not db.connect():
                return True, ""
            
            # ตรวจสอบว่ามีตาราง settings แล้วหรือยัง
            table_check = db.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not table_check:
                db.disconnect()
                return True, ""
            
            result = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'last_run_timestamp_30days'")
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
            
            db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp_30days', ?)", 
                       (current_time.strftime("%Y-%m-%d %H:%M:%S"),))
            db.disconnect()
            return True, ""
        except Exception as e:
            log_error(f"Error checking system clock in 30-day trial: {e}")
            return True, str(e)

    # ======================================================================
    # อ่าน/เขียน Trial Start Date — ไฟล์
    # ======================================================================

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
            log_error(f"Error writing 30-day trial file: {e}")
            return False

    # ======================================================================
    # อ่าน/เขียน Trial Start Date — ฐานข้อมูล
    # ======================================================================

    @staticmethod
    def _get_trial_db_date():
        """อ่านวันเริ่มต้นจากฐานข้อมูล"""
        try:
            db = DatabaseManager()
            if not db.connect():
                return None
            table_check = db.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not table_check:
                db.disconnect()
                return None
            result = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'trial_start_date_30days'")
            db.disconnect()
            if result:
                decoded = base64.b64decode(result['setting_value'].encode()).decode()
                return datetime.strptime(decoded, "%Y-%m-%d %H:%M:%S")
            return None
        except Exception as e:
            log_error(f"Error getting 30-day trial DB date: {e}")
            return None

    @staticmethod
    def _write_trial_db_date(dt):
        """บันทึกวันเริ่มต้นลงฐานข้อมูล"""
        try:
            db = DatabaseManager()
            if not db.connect():
                return False
            table_check = db.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if not table_check:
                db.disconnect()
                return False
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            encoded = base64.b64encode(dt_str.encode()).decode()
            db.execute("""
                INSERT OR REPLACE INTO settings (setting_key, setting_value)
                VALUES ('trial_start_date_30days', ?)
            """, (encoded,))
            db.disconnect()
            return True
        except Exception as e:
            log_error(f"Error writing 30-day trial DB date: {e}")
            return False



    # ======================================================================
    # ตรวจสอบ Activation หลัก
    # ======================================================================

    @staticmethod
    def check_activation():
        """ตรวจสอบสิทธิ์การใช้งาน (ลำดับแรก: ตรวจสอบ Full License Key, ลำดับสอง: ตรวจสอบ 30-Day Trial)"""
        # 1. ตรวจสอบว่ามี Full License Key หรือไม่
        full_key = LicenseManager.load_license()
        if full_key:
            hwid = HardwareID.generate_hwid()
            is_valid, msg, license_data = LicenseManager.validate_license_key(full_key, hwid)
            if is_valid:
                return True, f"✅ โปรแกรมเวอร์ชันเต็ม (Full Version) เปิดใช้งานสำเร็จ: {msg}", license_data

        clock_ok, clock_msg = LicenseManager.verify_system_clock()
        if not clock_ok:
            return False, clock_msg, None
            
        current_time = datetime.now()
        
        # อ่านจาก 3 แหล่ง (ปลอดภัยไม่ค้าง)
        file_date = LicenseManager._read_trial_file()
        db_date = LicenseManager._get_trial_db_date()
        reg_date = LicenseManager._read_registry_trial_date()
        
        # รวบรวมวันเริ่มต้นทั้งหมดที่มีอยู่
        all_dates = []
        if file_date:
            all_dates.append(file_date)
        if db_date:
            all_dates.append(db_date)
        if reg_date:
            all_dates.append(reg_date)
        
        if all_dates:
            trial_start = min(all_dates)
        else:
            trial_start = current_time
        
        # ซิงค์ทั้ง 3 แหล่งให้ตรงกัน (ใช้วันที่เก่าที่สุด)
        LicenseManager._write_trial_file(trial_start)
        LicenseManager._write_trial_db_date(trial_start)
        LicenseManager._write_registry_trial_date(trial_start)
            
        if current_time < trial_start:
            return False, f"ตรวจพบการโกงเวลาเครื่อง! เวลาปัจจุบันก่อนวันเริ่มทดลองใช้งาน (เริ่มทดลอง: {trial_start.strftime('%Y-%m-%d %H:%M:%S')})", None


            
        # คำนวณวันใช้งานคงเหลือ
        expire_date = (trial_start + timedelta(days=LicenseManager.TRIAL_DAYS)).date()
        current_date = current_time.date()
        days_left = (expire_date - current_date).days
        expire_date_str = expire_date.strftime("%Y-%m-%d")
        
        # สิทธิ์ฟังก์ชันทั้งหมดเปิดให้ใช้งานครบถ้วนเหมือนเวอร์ชันเต็ม
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
            "days_left": max(0, days_left)
        }
        
        if current_date > expire_date:
            return False, (
                f"เวอร์ชันทดลองใช้ฟรีหมดอายุแล้วเมื่อ {expire_date_str}\n\n"
                f"📦 ข้อมูลสินค้าและการขายของท่านยังคงอยู่ครบถ้วน\n"
                f"สามารถนำข้อมูลกลับมาใช้ได้เมื่อซื้อเวอร์ชันเต็ม"
            ), license_data
            
        return True, f"เวอร์ชันทดลองใช้งานคงเหลือ {days_left} วัน (หมดอายุ: {expire_date_str})", license_data

if __name__ == "__main__":
    is_ok, msg, data = LicenseManager.check_activation()
    print(f"30-Day Trial OK? {is_ok}")
    print(f"Message: {msg}")
    print(f"Data: {data}")
