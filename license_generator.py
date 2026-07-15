# -*- coding: utf-8 -*-
"""
License Key Generator - โปรแกรมสร้าง License Key (สำหรับผู้ขาย)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime, timedelta
from utils.license_system import LicenseManager
import json


class LicenseGeneratorApp(ctk.CTk):
    """โปรแกรมสร้าง License Key"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🔑 License Key Generator - สร้าง License สำหรับลูกค้า")
        self.geometry("900x750")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"+{x}+{y}")
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.create_widgets()
    
    def create_widgets(self):
        """สร้าง UI"""
        # === Header ===
        header = ctk.CTkFrame(self, fg_color="#1565C0", height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🔑 License Key Generator",
            font=("Sarabun", 32, "bold"),
            text_color="white"
        ).pack(side="left", padx=30, pady=30)
        
        ctk.CTkLabel(
            header,
            text="สำหรับผู้ขาย / Seller Only",
            font=("Sarabun", 16),
            text_color="#E3F2FD"
        ).pack(side="left", padx=(0, 30))
        
        # === Main Content ===
        main_frame = ctk.CTkFrame(self, fg_color="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Scrollable Frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        scroll_frame.pack(fill="both", expand=True)
        
        # === 1. Customer HWID Input ===
        section1 = ctk.CTkFrame(scroll_frame, fg_color="#E3F2FD", corner_radius=10)
        section1.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section1,
            text="📋 Step 1: ใส่ Hardware ID ของลูกค้า",
            font=("Sarabun", 20, "bold"),
            text_color="#1565C0"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            section1,
            text="ให้ลูกค้าส่ง HWID จากโปรแกรม POS มาให้คุณ",
            font=("Sarabun", 14),
            text_color="#424242"
        ).pack(pady=(0, 10))
        
        self.hwid_entry = ctk.CTkEntry(
            section1,
            font=("Courier New", 16),
            height=50,
            placeholder_text="XXXX-XXXX-XXXX-XXXX"
        )
        self.hwid_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        # === 2. License Configuration ===
        section2 = ctk.CTkFrame(scroll_frame, fg_color="#E8F5E9", corner_radius=10)
        section2.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section2,
            text="⚙️ Step 2: ตั้งค่า License",
            font=("Sarabun", 20, "bold"),
            text_color="#2E7D32"
        ).pack(pady=(20, 10))
        
        # วันหมดอายุ
        expire_frame = ctk.CTkFrame(section2, fg_color="transparent")
        expire_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            expire_frame,
            text="วันหมดอายุ (วัน):",
            font=("Sarabun", 16),
            width=200
        ).pack(side="left")
        
        self.expire_var = ctk.StringVar(value="365")
        expire_combo = ctk.CTkComboBox(
            expire_frame,
            values=["30", "90", "180", "365", "730", "3650", "ไม่จำกัด"],
            variable=self.expire_var,
            font=("Sarabun", 14),
            width=200
        )
        expire_combo.pack(side="left", padx=10)
        
        # Features
        features_frame = ctk.CTkFrame(section2, fg_color="white", corner_radius=10)
        features_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            features_frame,
            text="✨ Features ที่อนุญาต:",
            font=("Sarabun", 16, "bold")
        ).pack(pady=10)
        
        self.features = {}
        feature_list = [
            ("pos", "ระบบขายหน้าร้าน (POS)", True),
            ("inventory", "ระบบจัดการสินค้า", True),
            ("reports", "รายงานและสถิติ", True),
            ("barcode_scanner", "เครื่องยิงบาร์โค้ด", True),
            ("customer_display", "จอแสดงผลลูกค้า", True),
            ("printer", "เครื่องพิมพ์ใบเสร็จ", True),
            ("tax_invoice", "ใบกำกับภาษี", False),
            ("delivery_note", "ใบส่งของ", False)
        ]
        
        for key, label, default in feature_list:
            var = ctk.BooleanVar(value=default)
            self.features[key] = var
            
            ctk.CTkCheckBox(
                features_frame,
                text=label,
                variable=var,
                font=("Sarabun", 14)
            ).pack(anchor="w", padx=20, pady=5)
        
        # Customer Info (Optional)
        info_frame = ctk.CTkFrame(section2, fg_color="white", corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ ข้อมูลลูกค้า (ไม่บังคับ):",
            font=("Sarabun", 16, "bold")
        ).pack(pady=10)
        
        self.customer_name = ctk.CTkEntry(
            info_frame,
            placeholder_text="ชื่อลูกค้า/บริษัท",
            font=("Sarabun", 14),
            height=40
        )
        self.customer_name.pack(fill="x", padx=20, pady=5)
        
        self.customer_tel = ctk.CTkEntry(
            info_frame,
            placeholder_text="เบอร์โทร",
            font=("Sarabun", 14),
            height=40
        )
        self.customer_tel.pack(fill="x", padx=20, pady=(5, 15))
        
        # === 3. Generate Button ===
        generate_btn = ctk.CTkButton(
            scroll_frame,
            text="🎯 สร้าง License Key",
            font=("Sarabun", 20, "bold"),
            height=60,
            fg_color="#2E7D32",
            command=self.generate_license
        )
        generate_btn.pack(fill="x", pady=(0, 20))
        
        # === 4. Result Display ===
        section3 = ctk.CTkFrame(scroll_frame, fg_color="#FFF9C4", corner_radius=10)
        section3.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            section3,
            text="📄 License Key ที่สร้าง:",
            font=("Sarabun", 18, "bold"),
            text_color="#F57F17"
        ).pack(pady=(20, 10))
        
        self.result_text = ctk.CTkTextbox(
            section3,
            font=("Courier New", 11),
            height=150,
            fg_color="white"
        )
        self.result_text.pack(fill="x", padx=20, pady=(0, 10))
        
        # Copy & Save Buttons
        btn_frame = ctk.CTkFrame(section3, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            btn_frame,
            text="📋 Copy License Key",
            font=("Sarabun", 16),
            height=45,
            fg_color="#1565C0",
            command=self.copy_license
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="💾 บันทึกเป็นไฟล์",
            font=("Sarabun", 16),
            height=45,
            fg_color="#F57C00",
            command=self.save_to_file
        ).pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    def generate_license(self):
        """สร้าง License Key"""
        hwid = self.hwid_entry.get().strip()
        
        if not hwid:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาใส่ Hardware ID ของลูกค้า")
            return
        
        # ตรวจสอบรูปแบบ HWID
        if len(hwid.replace("-", "")) != 16:
            messagebox.showerror("ข้อผิดพลาด", "Hardware ID ไม่ถูกต้อง\nต้องเป็นรูปแบบ XXXX-XXXX-XXXX-XXXX")
            return
        
        # คำนวณวันหมดอายุ
        expire_str = self.expire_var.get()
        if expire_str == "ไม่จำกัด":
            expire_days = 36500  # 100 ปี
        else:
            expire_days = int(expire_str)
        
        # สร้าง features dict
        features = {key: var.get() for key, var in self.features.items()}
        
        # สร้าง License
        try:
            license_key = LicenseManager.generate_license_key(hwid, expire_days, features)
            
            # แสดงผล
            expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d")
            customer_name = self.customer_name.get().strip() or "ไม่ระบุ"
            customer_tel = self.customer_tel.get().strip() or "ไม่ระบุ"
            
            result = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                        LICENSE KEY GENERATED                          ║
╚═══════════════════════════════════════════════════════════════════════╝

📋 ข้อมูลลูกค้า:
   - ชื่อ: {customer_name}
   - เบอร์โทร: {customer_tel}

🖥️ Hardware ID:
   {hwid}

🔑 License Key:
   {license_key}

📅 วันที่สร้าง: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📅 วันหมดอายุ: {expire_date}
⏳ อายุการใช้งาน: {expire_days} วัน

✨ Features:
"""
            for key, label, _ in [
                ("pos", "ระบบขายหน้าร้าน (POS)", True),
                ("inventory", "ระบบจัดการสินค้า", True),
                ("reports", "รายงานและสถิติ", True),
                ("barcode_scanner", "เครื่องยิงบาร์โค้ด", True),
                ("customer_display", "จอแสดงผลลูกค้า", True),
                ("printer", "เครื่องพิมพ์ใบเสร็จ", True),
                ("tax_invoice", "ใบกำกับภาษี", False),
                ("delivery_note", "ใบส่งของ", False)
            ]:
                status = "✅ เปิด" if features[key] else "❌ ปิด"
                result += f"   {status} {label}\n"
            
            result += "\n" + "="*75 + "\n"
            result += "⚠️ หมายเหตุ: License Key นี้ผูกกับ HWID ของลูกค้าเท่านั้น\n"
            result += "   ไม่สามารถใช้กับเครื่องอื่นได้\n"
            
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", result)
            
            # เก็บ License Key ไว้
            self.current_license = {
                'hwid': hwid,
                'license_key': license_key,
                'customer_name': customer_name,
                'customer_tel': customer_tel,
                'expire_date': expire_date,
                'features': features,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            messagebox.showinfo("สำเร็จ! 🎉", "สร้าง License Key สำเร็จ!\n\nส่ง License Key ให้ลูกค้าเพื่อ Activate")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสร้าง License Key ได้\n\n{e}")
    
    def copy_license(self):
        """Copy License Key"""
        if not hasattr(self, 'current_license'):
            messagebox.showwarning("แจ้งเตือน", "กรุณาสร้าง License Key ก่อน")
            return
        
        self.clipboard_clear()
        self.clipboard_append(self.current_license['license_key'])
        messagebox.showinfo("สำเร็จ", "Copy License Key แล้ว!")
    
    def save_to_file(self):
        """บันทึกเป็นไฟล์"""
        if not hasattr(self, 'current_license'):
            messagebox.showwarning("แจ้งเตือน", "กรุณาสร้าง License Key ก่อน")
            return
        
        filename = filedialog.asksaveasfilename(
            title="บันทึก License Key",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"LICENSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_license, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("สำเร็จ", f"บันทึกไฟล์เรียบร้อย!\n\n{filename}")
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกไฟล์ได้\n\n{e}")


if __name__ == "__main__":
    app = LicenseGeneratorApp()
    app.mainloop()
