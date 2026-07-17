# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════╗
║          🔑 Standalone License Key Generator & Support Tool v3.0      ║
║          สำหรับผู้ขาย / Seller Only - Simplified Support Tool         ║
║                                                                       ║
║   ไฟล์เดียว ย้ายไปเครื่องไหนก็ได้ ไม่ต้องพึ่ง project หลัก           ║
║   Dependencies: Python 3.8+, customtkinter                           ║
║   ติดตั้ง: pip install customtkinter                                  ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

import uuid
import hashlib
import platform
import subprocess
import json
import base64
import sys
import os
import signal
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================================
# 1. GUI & Windows Settings
# =====================================================================
try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    import tkinter as tk
except ImportError:
    print("❌ ต้องติดตั้ง customtkinter ก่อน: pip install customtkinter")
    sys.exit(1)


# =====================================================================
# 2. HardwareID & License Core (Self-Contained)
# =====================================================================
class HardwareID:
    """จัดการ Hardware ID — Standalone"""

    @staticmethod
    def get_motherboard_uuid():
        try:
            if platform.system() == "Windows":
                try:
                    cmd = 'powershell -Command "Get-CimInstance Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"'
                    result = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
                    if result and result.lower() != "to be filled by o.e.m.":
                        return result
                except:
                    pass
                try:
                    cmd = "wmic csproduct get uuid"
                    result = subprocess.check_output(cmd, shell=True, timeout=10).decode()
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
                    cmd = 'powershell -Command "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty ProcessorId"'
                    result = subprocess.check_output(cmd, shell=True, timeout=10).decode().strip()
                    if result:
                        return result
                except:
                    pass
                try:
                    cmd = "wmic cpu get processorid"
                    result = subprocess.check_output(cmd, shell=True, timeout=10).decode()
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
    """จัดการ License Key — Standalone"""

    SECRET_KEY = b"POS_SYSTEM_2026_SECRET_KEY_DO_NOT_SHARE"

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


# =====================================================================
# 3. Main GUI Application
# =====================================================================
class KeyGenApp(ctk.CTk):
    """โปรแกรมสร้างคีย์และดูแลระบบสิทธิ์การใช้งาน (เวอร์ชันใช้งานง่าย)"""

    def __init__(self):
        super().__init__()

        self.title("🔑 KeyGen & License Support Tool (v3.0)")
        self.geometry("900x700")
        self.resizable(False, False)

        # Center Window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_layout()

    def create_layout(self):
        # === Header ===
        header = ctk.CTkFrame(self, fg_color="#1E3A8A", height=75, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🔑 StorePOS KeyGen & Support Tool",
            font=("Sarabun", 24, "bold"),
            text_color="white"
        ).pack(side="left", padx=25, pady=18)

        ctk.CTkLabel(
            header,
            text="เครื่องมือควบคุมสิทธิ์ & แก้ปัญหา POS ค้าง",
            font=("Sarabun", 12),
            text_color="#93C5FD"
        ).pack(side="right", padx=25, pady=25)

        # === Container (Split layout) ===
        container = ctk.CTkFrame(self, fg_color="#111827", corner_radius=0)
        container.pack(fill="both", expand=True)

        # Left Panel: Key Generation
        left_panel = ctk.CTkFrame(container, fg_color="#1F2937", corner_radius=12)
        left_panel.place(relx=0.02, rely=0.03, relwidth=0.46, relheight=0.62)

        ctk.CTkLabel(
            left_panel,
            text="🔑 สร้างรหัสลงทะเบียน (Generate Key)",
            font=("Sarabun", 16, "bold"),
            text_color="#60A5FA"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # HWID Input
        ctk.CTkLabel(left_panel, text="Hardware ID ลูกค้า:", font=("Sarabun", 13)).pack(anchor="w", padx=20)
        self.hwid_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX",
            font=("Courier New", 12),
            height=35
        )
        self.hwid_entry.pack(fill="x", padx=20, pady=(5, 12))

        # Expiry Combo
        ctk.CTkLabel(left_panel, text="อายุการใช้งาน (วัน):", font=("Sarabun", 13)).pack(anchor="w", padx=20)
        self.expire_var = ctk.StringVar(value="365")
        self.expire_combo = ctk.CTkComboBox(
            left_panel,
            values=["1", "7", "15", "30", "90", "180", "365", "ไม่จำกัด"],
            variable=self.expire_var,
            font=("Sarabun", 13),
            height=35
        )
        self.expire_combo.pack(fill="x", padx=20, pady=(5, 15))

        # Generate Button
        ctk.CTkButton(
            left_panel,
            text="🎯 สร้าง License Key",
            font=("Sarabun", 14, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=40,
            command=self.generate_key
        ).pack(fill="x", padx=20, pady=10)

        # Copy Result Button
        ctk.CTkButton(
            left_panel,
            text="📋 คัดลอก Key ปัจจุบัน",
            font=("Sarabun", 13),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            height=35,
            command=self.copy_key
        ).pack(fill="x", padx=20, pady=5)


        # Right Panel: System Support (The 3 requested options)
        right_panel = ctk.CTkFrame(container, fg_color="#1F2937", corner_radius=12)
        right_panel.place(relx=0.52, rely=0.03, relwidth=0.46, relheight=0.62)

        ctk.CTkLabel(
            right_panel,
            text="🛠️ เครื่องมือบำรุงรักษา (Maintenance)",
            font=("Sarabun", 16, "bold"),
            text_color="#F87171"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Button 1: Force Close POS (KillProcess)
        ctk.CTkButton(
            right_panel,
            text="⚡ ปิดโปรแกรมที่ค้างอยู่ (Kill Process)",
            font=("Sarabun", 13, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            height=45,
            command=self.run_kill_process
        ).pack(fill="x", padx=20, pady=12)

        # Button 2: Deactivate License (ถอนไลเซ้น)
        ctk.CTkButton(
            right_panel,
            text="🚫 ถอนไลเซ้น (Deactivate License)",
            font=("Sarabun", 13, "bold"),
            fg_color="#F59E0B",
            hover_color="#D97706",
            height=45,
            command=self.run_deactivate_license
        ).pack(fill="x", padx=20, pady=12)

        # Button 3: Reset Registration & Clear Database memory (ล้างความจำเครื่อง)
        ctk.CTkButton(
            right_panel,
            text="🧹 ล้างความจำเครื่อง (Reset Activation & DB)",
            font=("Sarabun", 13, "bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            height=45,
            command=self.run_reset_license_cache
        ).pack(fill="x", padx=20, pady=12)


        # Bottom Panel: Result Key & System Log
        bottom_panel = ctk.CTkFrame(container, fg_color="#1F2937", corner_radius=12)
        bottom_panel.place(relx=0.02, rely=0.68, relwidth=0.96, relheight=0.28)

        # Key Output / Logs Display (Unified Log screen)
        self.log_text = ctk.CTkTextbox(
            bottom_panel,
            font=("Courier New", 12),
            fg_color="#111827",
            text_color="#10B981"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.log("💡 ยินดีต้อนรับเข้าสู่ระบบ KeyGen & Support Tool\nกรุณาเลือกฟังก์ชันการทำงานที่ต้องการ...")
        
        # Bind copy menus
        self.bind_context_menu(self.hwid_entry)
        self.bind_context_menu(self.log_text)

    def log(self, message):
        """แสดง Log บนหน้าต่างด้านล่าง"""
        self.log_text.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")

    def bind_context_menu(self, widget):
        inner_widget = widget._entry if hasattr(widget, "_entry") else widget._textbox
        menu = tk.Menu(inner_widget, tearoff=0)
        menu.add_command(label="ตัด (Cut)", command=lambda: inner_widget.event_generate("<<Cut>>"))
        menu.add_command(label="คัดลอก (Copy)", command=lambda: inner_widget.event_generate("<<Copy>>"))
        menu.add_command(label="วาง (Paste)", command=lambda: inner_widget.event_generate("<<Paste>>"))
        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        inner_widget.bind("<Button-3>", show_menu)

    # ==================================================================
    # Core Operations
    # ==================================================================
    def generate_key(self):
        hwid = self.hwid_entry.get().strip()
        if not hwid:
            messagebox.showerror("ผิดพลาด", "กรุณาระบุ Hardware ID ของลูกค้าก่อน")
            return
        
        if len(hwid.replace("-", "")) != 32:
            messagebox.showerror("ผิดพลาด", "รูปแบบ Hardware ID ไม่ถูกต้อง")
            return

        expire_str = self.expire_var.get()
        if expire_str == "ไม่จำกัด":
            expire_days = 36500
        else:
            try:
                expire_days = int(expire_str)
            except:
                expire_days = 365

        try:
            key = LicenseManager.generate_license_key(hwid, expire_days)
            self.current_key = key
            
            self.log_text.delete("1.0", "end")
            self.log(f"🔑 สร้างรหัสสำเร็จ (อายุการใช้งาน {expire_str} วัน):")
            self.log_text.insert("end", f"\n{key}\n\n")
            self.log("📋 ทำการคัดลอก Key ไปยัง Clipboard อัตโนมัติเรียบร้อย")
            
            self.clipboard_clear()
            self.clipboard_append(key)
        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถสร้าง License Key ได้: {e}")

    def copy_key(self):
        if hasattr(self, 'current_key'):
            self.clipboard_clear()
            self.clipboard_append(self.current_key)
            self.log("📋 คัดลอกรหัสสำเร็จ")
        else:
            messagebox.showwarning("คำเตือน", "กรุณาสร้าง License Key ก่อน")

    def run_kill_process(self):
        """⚡ ฟีเจอร์ที่ 3: ปิดโปรแกรมที่ค้างอยู่ (Kill Process)"""
        self.log("⚡ กำลังปิดโปรแกรม POS ที่อาจค้างอยู่...")
        my_pid = os.getpid()
        killed_count = 0
        
        # ปิด StorePOS.exe
        try:
            res = subprocess.call("taskkill /F /IM StorePOS.exe /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res == 0:
                killed_count += 1
        except:
            pass
            
        # ปิด Python main.py หรือ main_trial.py
        if platform.system() == "Windows":
            try:
                # ใช้งาน PowerShell ดึง Process ID และ CommandLine
                cmd = ["powershell", "-NoProfile", "-Command",
                       "Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='pythonw.exe'\" | ForEach-Object { \"$($_.ProcessId)||$($_.CommandLine)\" }"]
                output = subprocess.check_output(cmd, creationflags=0x08000000).decode(errors='ignore')
                lines = output.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or "||" not in line:
                        continue
                    parts = line.split("||", 1)
                    if len(parts) < 2:
                        continue
                    try:
                        pid = int(parts[0].strip())
                        cmdline = parts[1].strip().lower()
                        
                        if pid == my_pid:
                            continue
                            
                        if "main.py" in cmdline or "main_trial.py" in cmdline:
                            os.kill(pid, signal.SIGTERM)
                            killed_count += 1
                    except:
                        pass
            except Exception as e:
                # ลอง Fallback กลับไปใช้ wmic ถ้ามี
                try:
                    cmd_wmic = "wmic process where \"name='python.exe' or name='pythonw.exe'\" get processid,commandline"
                    output = subprocess.check_output(cmd_wmic, shell=True, timeout=5).decode(errors='ignore')
                    lines = output.strip().split('\n')
                    for line in lines[1:]:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) < 2:
                            continue
                        try:
                            pid = int(parts[-1])
                            cmdline = " ".join(parts[:-1]).lower()
                            
                            if pid == my_pid:
                                continue
                                
                            if "main.py" in cmdline or "main_trial.py" in cmdline:
                                os.kill(pid, signal.SIGTERM)
                                killed_count += 1
                        except:
                            pass
                except Exception as ex_wmic:
                    self.log(f"❌ เกิดข้อผิดพลาดในการตรวจสอบ Process: {ex_wmic}")
                
        self.log(f"✅ ทำการปิดโปรแกรมที่ค้างในระบบแล้ว (รวม {killed_count} processes)")
        messagebox.showinfo("สำเร็จ", f"ปิดโปรแกรม POS ค้างในเบื้องหลังเรียบร้อยแล้ว (รวม {killed_count} รายการ)")

    def _get_all_possible_license_paths(self):
        """สแกนหาไฟล์ License ทั้งหมดในตำแหน่งยอดนิยม"""
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
            
        found_files = []
        seen = set()
        for p in possible_paths:
            try:
                normalized = p.resolve().absolute()
            except:
                normalized = p.absolute()
            if normalized not in seen:
                seen.add(normalized)
                if normalized.exists():
                    found_files.append(normalized)
        return found_files

    def run_deactivate_license(self):
        """🚫 ฟีเจอร์ที่ 1: ถอนไลเซ้น (Deactivate License)"""
        # ก่อนทำงาน ให้ Kill POS ก่อนเพื่อไม่ให้ไฟล์ล็อก
        self.run_kill_process()
        
        found_files = self._get_all_possible_license_paths()
        
        # สอบถามว่าจะเลือกไฟล์เองหรือสแกนอัตโนมัติ
        select_mode = messagebox.askyesnocancel(
            "ถอนไลเซ้น",
            "คุณต้องการเลือกไฟล์ License เองใช่หรือไม่?\n\n"
            "• กด 'Yes' เพื่อเลือกไฟล์ด้วยตนเอง (Manual Select)\n"
            "• กด 'No' เพื่อใช้ระบบถอนสิทธิ์อัตโนมัติ (Auto Scan)\n"
            "• กด 'Cancel' เพื่อยกเลิก"
        )
        
        if select_mode is None:
            return
            
        if select_mode: # Manual Select
            file_path = filedialog.askopenfilename(
                title="เลือกไฟล์ License ที่ต้องการถอน",
                filetypes=[("License files", "*.license"), ("All files", "*.*")]
            )
            if not file_path:
                return
            found_files = [Path(file_path)]
            
        if not found_files:
            messagebox.showinfo("ไม่พบสิทธิ์", "ระบบตรวจไม่พบการติดตั้ง License ในโฟลเดอร์ใดๆ เลย")
            return
            
        confirm = messagebox.askyesno(
            "ยืนยันการถอน License",
            f"คุณแน่ใจว่าต้องการลบไฟล์สิทธิ์การลงทะเบียนใช่หรือไม่?\n"
            f"พบทั้งหมด: {len(found_files)} ตำแหน่ง"
        )
        if not confirm:
            return
            
        deleted_count = 0
        for f in found_files:
            try:
                if f.exists():
                    f.unlink()
                    deleted_count += 1
                    self.log(f"🗑️ ลบไฟล์สิทธิ์: {f}")
            except Exception as e:
                self.log(f"❌ ถอนสิทธิ์ไม่สำเร็จ ณ พาธ {f}: {e}")
                
        self.log(f"✅ ทำการถอนไลเซ้นในระบบเสร็จสิ้น (สำเร็จ {deleted_count} ไฟล์)")
        messagebox.showinfo("สำเร็จ", f"ถอนไลเซ้นในเครื่องสำเร็จแล้ว (ลบทั้งหมด {deleted_count} จุด)")

    def run_reset_license_cache(self):
        """🧹 ฟีเจอร์ที่ 2: ล้างสิ่งที่เครื่องจำอยู่เพื่อลงทะเบียนใหม่ (Reset Database & Trial File Cache)"""
        # ปิดกระบวนการค้างก่อน
        self.run_kill_process()
        
        confirm = messagebox.askyesno(
            "ล้างข้อมูลเครื่อง",
            "⚠️ การทำแบบนี้จะลบข้อมูลประวัติการทำงานของเวลาเครื่อง วันที่เริ่มใช้ตัวทดลองใช้ (Trial)\n"
            "รวมถึงถอนไลเซ้นออกทั้งหมด เพื่อเตรียมการลงทะเบียนใหม่\n\n"
            "ยืนยันการล้างความจำเครื่องทั้งหมดใช่หรือไม่?"
        )
        if not confirm:
            return
            
        self.log("🧹 เริ่มการล้างความจำเครื่อง...")
        
        # 1. ลบไฟล์ License ทั้งหมด
        license_files = self._get_all_possible_license_paths()
        deleted_licenses = 0
        for f in license_files:
            try:
                f.unlink()
                deleted_licenses += 1
                self.log(f"🗑️ ลบไฟล์ License: {f}")
            except:
                pass
                
        # 2. ลบไฟล์ทดลองใช้ฟรี .trial ทั้งหมด
        trial_paths = []
        import os
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
            trial_paths.append(Path(folder) / "data" / ".trial")
        trial_paths.append(Path("data/.trial").absolute())
        
        deleted_trials = 0
        seen = set()
        for p in trial_paths:
            try:
                normalized = p.resolve().absolute()
            except:
                normalized = p.absolute()
            if normalized not in seen:
                seen.add(normalized)
                if normalized.exists():
                    try:
                        normalized.unlink()
                        deleted_trials += 1
                        self.log(f"🗑️ ลบไฟล์ทดลองใช้งาน: {normalized}")
                    except:
                        pass
                        
        # 3. ล้างตารางสิทธิ์และการแจ้งเวลาในฐานข้อมูล SQLite
        db_paths = []
        for folder in standard_folders:
            db_paths.append(Path(folder) / "data" / "database.db")
        db_paths.append(Path("data/database.db").absolute())
        
        cleaned_dbs = 0
        seen_dbs = set()
        for db_path in db_paths:
            try:
                normalized = db_path.resolve().absolute()
            except:
                normalized = db_path.absolute()
            if normalized not in seen_dbs:
                seen_dbs.add(normalized)
                if normalized.exists():
                    try:
                        conn = sqlite3.connect(normalized)
                        cursor = conn.cursor()
                        # ลบประวัติ
                        cursor.execute("DELETE FROM settings WHERE setting_key = 'last_run_timestamp'")
                        cursor.execute("DELETE FROM settings WHERE setting_key = 'trial_start_date'")
                        try:
                            cursor.execute("DELETE FROM license_logs")
                        except:
                            pass
                        conn.commit()
                        conn.execute("VACUUM")
                        conn.close()
                        cleaned_dbs += 1
                        self.log(f"🧹 ล้างฐานข้อมูลสิทธิ์: {normalized}")
                    except Exception as e:
                        self.log(f"❌ ไม่สามารถรีเซ็ตฐานข้อมูล {normalized}: {e}")
                        
        self.log(f"✅ ล้างเสร็จสิ้น: ลบไฟล์ License ({deleted_licenses}), ไฟล์ทดลอง ({deleted_trials}), รีเซ็ต DB ({cleaned_dbs})")
        messagebox.showinfo("สำเร็จ", "ล้างความจำและค่าประวัติเครื่องเพื่อการลงทะเบียนใหม่เสร็จสิ้นแล้ว!")


if __name__ == "__main__":
    app = KeyGenApp()
    app.mainloop()
