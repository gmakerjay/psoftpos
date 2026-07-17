# -*- coding: utf-8 -*-
"""
Hardware ID & License System
ระบบตรวจสอบ Hardware ID และ License Key - Security Enhanced & Tolerant Matching
"""

import uuid
import hashlib
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
import base64
from database.db_manager import DatabaseManager
from utils.logger import log_error, log_info

class HardwareID:
    """จัดการ Hardware ID"""
    
    @staticmethod
    def get_motherboard_uuid():
        """ดึง UUID ของ Motherboard"""
        try:
            if platform.system() == "Windows":
                try:
                    cmd = "powershell -Command \"Get-CimInstance Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID\""
                    result = subprocess.check_output(cmd, shell=True).decode().strip()
                    if result and result.lower() != "to be filled by o.e.m.":
                        return result
                except:
                    pass
                
                cmd = "wmic csproduct get uuid"
                result = subprocess.check_output(cmd, shell=True).decode()
                uuid_line = result.split('\n')[1].strip()
                if uuid_line and uuid_line.lower() != "to be filled by o.e.m.":
                    return uuid_line
            return "UNKNOWN_MB_UUID"
        except:
            return "UNKNOWN_MB_UUID"
            
    @staticmethod
    def get_cpu_id():
        """ดึง CPU ID"""
        try:
            if platform.system() == "Windows":
                try:
                    cmd = "powershell -Command \"Get-CimInstance Win32_Processor | Select-Object -ExpandProperty ProcessorId\""
                    result = subprocess.check_output(cmd, shell=True).decode().strip()
                    if result:
                        return result
                except:
                    pass
                
                cmd = "wmic cpu get processorid"
                result = subprocess.check_output(cmd, shell=True).decode()
                cpu_id = result.split('\n')[1].strip()
                if cpu_id:
                    return cpu_id
            return "UNKNOWN_CPU"
        except:
            return "UNKNOWN_CPU"

    @staticmethod
    def get_disk_serial():
        """ดึง Serial Number ของไดรฟ์ C: แบบ Native (ctypes) เพื่อความทนทานต่อการย้าย/ลง Windows ใหม่"""
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
        """ดึง Windows Machine GUID จาก Registry"""
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
        """สร้าง HWID แบบ Tolerant (4 กลุ่มจาก 4 ฮาร์ดแวร์หลัก)"""
        mb = HardwareID.get_motherboard_uuid()
        cpu = HardwareID.get_cpu_id()
        disk = HardwareID.get_disk_serial()
        guid = HardwareID.get_machine_guid()
        
        # MAC fallback
        fallback = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:8].upper()
        
        mb_h = hashlib.sha256(mb.encode()).hexdigest()[:8].upper() if mb != "UNKNOWN_MB_UUID" else fallback
        cpu_h = hashlib.sha256(cpu.encode()).hexdigest()[:8].upper() if cpu != "UNKNOWN_CPU" else fallback
        disk_h = hashlib.sha256(disk.encode()).hexdigest()[:8].upper() if disk != "UNKNOWN_DISK" else fallback
        guid_h = hashlib.sha256(guid.encode()).hexdigest()[:8].upper() if guid != "UNKNOWN_GUID" else fallback
        
        return f"{mb_h}-{cpu_h}-{disk_h}-{guid_h}"

    @staticmethod
    def get_machine_id():
        """ดึง Machine ID (เพื่อความเข้ากันได้ย้อนหลัง)"""
        return HardwareID.get_motherboard_uuid()

    @staticmethod
    def get_motherboard_serial():
        """ดึง Serial Number ของ Motherboard (เพื่อความเข้ากันได้ย้อนหลัง)"""
        return HardwareID.get_motherboard_uuid()


class LicenseManager:
    """จัดการ License Key"""
    
    LICENSE_FILE = Path("data/.license")
    MANUAL_LICENSE_PATH = None
    # คีย์ลับสำหรับสร้างและตรวจสอบ Signature
    SECRET_KEY = b"POS_SYSTEM_2026_SECRET_KEY_DO_NOT_SHARE"

    @staticmethod
    def set_manual_license_path(path):
        """กำหนดพาธของไฟล์ License ด้วยตนเอง"""
        if path:
            LicenseManager.MANUAL_LICENSE_PATH = Path(path)
        else:
            LicenseManager.MANUAL_LICENSE_PATH = None

    @staticmethod
    def get_license_file_path(write_mode=False):
        """ค้นหาตำแหน่งไฟล์ License ที่มีอยู่จริงบนเครื่อง"""
        if LicenseManager.MANUAL_LICENSE_PATH:
            return LicenseManager.MANUAL_LICENSE_PATH
            
        import sys
        import os
        
        possible_paths = []
        try:
            if sys.argv and sys.argv[0]:
                possible_paths.append(Path(sys.argv[0]).parent.absolute() / "data" / ".license")
        except:
            pass
            
        try:
            if getattr(sys, 'frozen', False):
                possible_paths.append(Path(sys.executable).parent.absolute() / "data" / ".license")
        except:
            pass
            
        try:
            possible_paths.append(Path(__file__).parent.parent.absolute() / "data" / ".license")
        except:
            pass
            
        try:
            possible_paths.append(Path("data/.license").absolute())
        except:
            pass
            
        standard_folders = [
            "C:/StorePOS",
            "D:/StorePOS",
            os.path.expanduser("~/Documents/store-pos"),
            os.path.expanduser("~/Documents/StorePOS"),
            os.path.expanduser("~/Desktop/store-pos"),
            os.path.expanduser("~/Desktop/StorePOS"),
            "C:/Program Files/StorePOS",
            "C:/Program Files (x86)/StorePOS"
        ]
        for folder in standard_folders:
            try:
                possible_paths.append(Path(folder) / "data" / ".license")
            except:
                pass
                
        unique_paths = []
        seen = set()
        for p in possible_paths:
            try:
                normalized = p.resolve().absolute()
            except:
                normalized = p.absolute()
            if normalized not in seen:
                seen.add(normalized)
                unique_paths.append(normalized)
                
        if not write_mode:
            for p in unique_paths:
                if p.exists():
                    return p
                    
        return unique_paths[0]
    
    @staticmethod
    def log_license_action(action, license_key=None, hwid=None, details=""):
        """บันทึกประวัติการกระทำของ License ลงฐานข้อมูล"""
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
        """
        ตรวจสอบการจับคู่ HWID แบบ Tolerant (ผ่านเมื่อตรงอย่างน้อย 3 ใน 4 กลุ่ม)
        """
        curr_parts = current_hwid.split("-")
        targ_parts = registered_hwid.split("-")
        
        if len(curr_parts) != 4 or len(targ_parts) != 4:
            return False
            
        matches = 0
        for c_part, t_part in zip(curr_parts, targ_parts):
            if c_part == t_part:
                matches += 1
                
        return matches >= 3

    @staticmethod
    def generate_license_key(hwid, expire_days=365, features=None):
        """
        สร้าง License Key สำหรับ HWID นี้
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
        
        # สร้าง Signature โดยผูกกับ registered HWID และ Secret Key
        signature = hashlib.sha256(
            (encoded + hwid + LicenseManager.SECRET_KEY.decode()).encode()
        ).hexdigest()[:16]
        
        # รวม License Key: SIGNATURE-ENCODED_DATA
        license_key = f"{signature.upper()}-{encoded}"
        
        return license_key
    
    @staticmethod
    def validate_license_key(license_key, current_hwid):
        """
        ตรวจสอบ License Key ว่าถูกต้องและตรงกับ HWID นี้หรือไม่ (รองรับการ Binding หลายเครื่องและการจับคู่แบบ Tolerant)
        """
        try:
            # แยก Signature และ Data
            parts = license_key.split('-', 1)
            if len(parts) != 2:
                return False, "รูปแบบ License Key ไม่ถูกต้อง", None
            
            signature, encoded_data = parts
            
            # Decode Data ก่อนเพื่อหา registered HWID
            json_data = base64.b64decode(encoded_data.encode()).decode()
            license_data = json.loads(json_data)
            
            registered_hwid = license_data.get('hwid', '')
            
            # ตรวจสอบ Signature
            expected_sig = hashlib.sha256(
                (encoded_data + registered_hwid + LicenseManager.SECRET_KEY.decode()).encode()
            ).hexdigest()[:16].upper()
            
            if signature != expected_sig:
                return False, "License Key ไม่ถูกต้อง (Signature ไม่ตรง)", None
            
            # ตรวจสอบ HWID แบบรองรับ Multi-binding และ Tolerant Matching
            if isinstance(registered_hwid, str):
                if ',' in registered_hwid:
                    registered_hwids = [h.strip() for h in registered_hwid.split(',')]
                else:
                    registered_hwids = [registered_hwid]
            else:
                registered_hwids = []
                
            hwid_matched = False
            for reg_hwid in registered_hwids:
                if LicenseManager.check_hwid_match(current_hwid, reg_hwid):
                    hwid_matched = True
                    break
                    
            if not hwid_matched:
                return False, "License Key นี้ไม่ตรงกับฮาร์ดแวร์ของเครื่องนี้", None
            
            # ตรวจสอบวันหมดอายุ (หมดอายุเมื่อขึ้นวันใหม่หลังจากวันหมดอายุ)
            expire_date = datetime.strptime(license_data['expire_date'], "%Y-%m-%d")
            if datetime.now().date() > expire_date.date():
                return False, f"License หมดอายุแล้ว (หมดอายุ: {license_data['expire_date']})", None
            
            days_left = (expire_date.date() - datetime.now().date()).days
            
            return True, f"License ถูกต้อง (เหลืออีก {days_left} วัน)", license_data
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการตรวจสอบ: {str(e)}", None
    
    @staticmethod
    def get_expiry_warning(license_data):
        """
        ตรวจสอบว่า License ใกล้หมดอายุหรือไม่ และส่งข้อมูลระดับการเตือนกลับ
        
        กฎการแจ้งเตือน:
        - License ทดสอบ (1-7 วัน): แจ้งเตือนเมื่อเหลือ ≤ 1 วัน (หรือในวันสุดท้าย)
        - License ระยะสั้น (15-180 วัน): แจ้งเตือนเมื่อเหลือ ≤ 3 วัน
        - License ระยะยาว (365+ วัน): แจ้งเตือนเมื่อเหลือ ≤ 7 วัน
        
        Returns:
            dict: {
                'level': 'critical' | 'warning' | 'none',
                'days_left': int,
                'expire_date': str,
                'message': str,
                'title': str
            }
        """
        try:
            expire_date = datetime.strptime(license_data['expire_date'], "%Y-%m-%d")
            issued_date_str = license_data.get('issued_date', '')
            
            now = datetime.now()
            days_left = (expire_date.date() - now.date()).days
            
            # คำนวณจำนวนวันทั้งหมดของ License (จากวันออก ถึง วันหมดอายุ)
            if issued_date_str:
                try:
                    issued_date = datetime.strptime(issued_date_str[:10], "%Y-%m-%d")
                    total_days = (expire_date - issued_date).days
                except:
                    total_days = days_left
            else:
                total_days = days_left
            
            # กำหนดเกณฑ์แจ้งเตือนตามประเภท License
            if total_days <= 7:
                # License ทดสอบ (1-7 วัน): เตือนเมื่อเหลือ ≤ 1 วัน
                warn_threshold = 1
                license_type = "ทดสอบ"
            elif total_days <= 180:
                # License ระยะสั้น (15-180 วัน): เตือนเมื่อเหลือ ≤ 3 วัน
                warn_threshold = 3
                license_type = "ระยะสั้น"
            else:
                # License ระยะยาว (365+ วัน): เตือนเมื่อเหลือ ≤ 7 วัน
                warn_threshold = 7
                license_type = "ระยะยาว"
            
            expire_date_str = expire_date.strftime("%d/%m/%Y")
            
            if days_left < 0:
                return {
                    'level': 'expired',
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': '⛔ License หมดอายุแล้ว!',
                    'message': (
                        f"License ของคุณหมดอายุแล้ว!\n\n"
                        f"📅 วันหมดอายุ: {expire_date_str}\n"
                        f"📦 ประเภท License: {license_type} ({total_days} วัน)\n\n"
                        f"❌ กรุณาติดต่อผู้ขายเพื่อต่ออายุ License ใหม่\n"
                        f"โปรแกรมจะไม่สามารถใช้งานได้จนกว่าจะ Activate ใหม่"
                    )
                }
            elif days_left <= warn_threshold:
                # ระดับ critical = วันสุดท้าย, warning = ยังมีเวลาอีกเล็กน้อย
                level = 'critical' if days_left <= 1 else 'warning'
                
                if days_left == 0:
                    days_text = "วันนี้เป็นวันสุดท้าย!"
                elif days_left == 1:
                    days_text = "เหลืออีก 1 วันเท่านั้น!"
                else:
                    days_text = f"เหลืออีก {days_left} วัน"
                
                return {
                    'level': level,
                    'days_left': days_left,
                    'expire_date': expire_date_str,
                    'total_days': total_days,
                    'license_type': license_type,
                    'title': f'⚠️ License ใกล้หมดอายุ! ({days_text})',
                    'message': (
                        f"⏰ License ของคุณใกล้จะหมดอายุแล้ว!\n\n"
                        f"📅 วันหมดอายุ: {expire_date_str}\n"
                        f"⏳ {days_text}\n"
                        f"📦 ประเภท License: {license_type} ({total_days} วัน)\n\n"
                        f"⚠️ กรุณาติดต่อผู้ขายเพื่อต่ออายุก่อนหมดเขต\n"
                        f"หากไม่ต่ออายุ โปรแกรมจะหยุดทำงานเมื่อ License หมดอายุ"
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
        """บันทึก License Key ลงไฟล์และบันทึก Log"""
        try:
            path = LicenseManager.get_license_file_path(write_mode=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # เข้ารหัสก่อนบันทึก
            encrypted = base64.b64encode(license_key.encode()).decode()
            
            with open(path, 'w') as f:
                f.write(encrypted)
                
            hwid = HardwareID.generate_hwid()
            LicenseManager.log_license_action("ACTIVATE", license_key, hwid, "คีย์ผ่านการ Activate สำเร็จ")
            return True
        except Exception as e:
            print(f"Error saving license: {e}")
            return False
    
    @staticmethod
    def load_license():
        """โหลด License Key จากไฟล์"""
        try:
            path = LicenseManager.get_license_file_path()
            if not path.exists():
                return None
            
            with open(path, 'r') as f:
                encrypted = f.read()
            
            # ถอดรหัส
            license_key = base64.b64decode(encrypted.encode()).decode()
            return license_key
        except:
            return None
    
    @staticmethod
    def delete_license():
        """ลบ License Key และบันทึก Log (ค้นหาและลบทุกตำแหน่งที่พบบนเครื่อง)"""
        try:
            license_key = LicenseManager.load_license()
            deleted_any = False
            
            # 1. ลบจาก MANUAL_LICENSE_PATH ก่อนถ้ามี
            if LicenseManager.MANUAL_LICENSE_PATH and LicenseManager.MANUAL_LICENSE_PATH.exists():
                try:
                    LicenseManager.MANUAL_LICENSE_PATH.unlink()
                    deleted_any = True
                except:
                    pass
            
            # 2. ค้นหาในทุกตำแหน่งที่เป็นไปได้
            import sys
            import os
            possible_paths = []
            try:
                if sys.argv and sys.argv[0]:
                    possible_paths.append(Path(sys.argv[0]).parent.absolute() / "data" / ".license")
            except: pass
            try:
                if getattr(sys, 'frozen', False):
                    possible_paths.append(Path(sys.executable).parent.absolute() / "data" / ".license")
            except: pass
            try:
                possible_paths.append(Path(__file__).parent.parent.absolute() / "data" / ".license")
            except: pass
            try:
                possible_paths.append(Path("data/.license").absolute())
            except: pass
            
            standard_folders = [
                "C:/StorePOS",
                "D:/StorePOS",
                os.path.expanduser("~/Documents/store-pos"),
                os.path.expanduser("~/Documents/StorePOS"),
                os.path.expanduser("~/Desktop/store-pos"),
                os.path.expanduser("~/Desktop/StorePOS"),
                "C:/Program Files/StorePOS",
                "C:/Program Files (x86)/StorePOS"
            ]
            for folder in standard_folders:
                possible_paths.append(Path(folder) / "data" / ".license")
                
            seen = set()
            for p in possible_paths:
                try:
                    normalized = p.resolve().absolute()
                except:
                    normalized = p.absolute()
                if normalized not in seen:
                    seen.add(normalized)
                    if normalized.exists():
                        try:
                            normalized.unlink()
                            deleted_any = True
                        except Exception as e:
                            print(f"Error unlinking {normalized}: {e}")
                            
            hwid = HardwareID.generate_hwid()
            LicenseManager.log_license_action("DISABLE", license_key, hwid, "ทำการปิดใช้งาน (Disable) License ในระบบ")
            return deleted_any
        except Exception as e:
            print(f"Error deleting license: {e}")
            return False
            
    @staticmethod
    def transfer_license():
        """โอนย้าย License - ปิดใช้งานและสร้าง Transfer Code เพื่อส่งยืนยันกับผู้ขาย"""
        try:
            license_key = LicenseManager.load_license()
            if not license_key:
                return False, "ไม่พบ License ที่เปิดใช้งานอยู่", None
                
            hwid = HardwareID.generate_hwid()
            
            # ลบ License ทุกจุด
            LicenseManager.delete_license()
                
            # สร้าง deactivation signature
            deact_data = f"DEACTIVATE-{hwid}-{datetime.now().strftime('%Y-%m-%d')}"
            deact_sig = hashlib.sha256((deact_data + LicenseManager.SECRET_KEY.decode()).encode()).hexdigest()[:16].upper()
            transfer_code = f"TRANSFER-{deact_sig}-{base64.b64encode(deact_data.encode()).decode()}"
            
            LicenseManager.log_license_action("TRANSFER", license_key, hwid, f"โอนย้าย License - Transfer Code: {transfer_code}")
            return True, "ทำการยกเลิก License บนเครื่องนี้เพื่อการโอนย้ายแล้ว", transfer_code
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}", None

    @staticmethod
    def verify_system_clock():
        """
        ตรวจสอบความถูกต้องของเวลาเครื่อง (ป้องกันการย้อนเวลาเพื่อยืดอายุ License)
        """
        try:
            db = DatabaseManager()
            db.connect()
            
            # ดึงค่าเวลาการทำงานล่าสุดจากฐานข้อมูล
            result = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'last_run_timestamp'")
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
            
            # อัปเดตเวลาล่าสุดลงฐานข้อมูล
            db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('last_run_timestamp', ?)", 
                       (current_time.strftime("%Y-%m-%d %H:%M:%S"),))
            db.disconnect()
            return True, ""
        except Exception as e:
            # หากมีข้อผิดพลาด ให้ปล่อยผ่านแบบแจ้งเตือนเพื่อไม่ให้ระบบหลักค้าง
            log_error(f"Error checking system clock: {e}")
            return True, str(e)

    @staticmethod
    def check_activation():
        """
        ตรวจสอบว่าโปรแกรมถูก Activate แล้วหรือไม่
        """
        # 1. ตรวจสอบการย้อนเวลาก่อน
        clock_ok, clock_msg = LicenseManager.verify_system_clock()
        if not clock_ok:
            return False, clock_msg, None
            
        # 2. โหลด License
        license_key = LicenseManager.load_license()
        if not license_key:
            return False, "ไม่พบ License Key - กรุณา Activate โปรแกรม", None
        
        # 3. ดึง HWID ปัจจุบัน
        hwid = HardwareID.generate_hwid()
        
        # 4. ตรวจสอบ License
        return LicenseManager.validate_license_key(license_key, hwid)

# ทดสอบ
if __name__ == "__main__":
    print("="*60)
    print("Hardware ID & License System")
    print("="*60)
    
    hwid = HardwareID.generate_hwid()
    print(f"\nYour formatted HWID: {hwid}")

