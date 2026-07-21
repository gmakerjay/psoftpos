# -*- coding: utf-8 -*-
"""
Splash Screen / Startup Progress Window for StorePOS (Multi-threaded Edition)
แสดงหลอด Progress Bar และข้อความสถานะขณะกำลังโหลดเข้าสู่โปรแกรม
รองรับคอมพิวเตอร์รุ่นเก่าแบบ Multi-threading เพื่อไม่ให้หน้าจอค้างหรือ Not Responding
"""

import sys
import os
import time
import queue
import threading
import customtkinter as ctk

class SplashScreen:
    """หน้าต่างแสดงสถานะการโหลดโปรแกรม (Splash Screen) พร้อม Progress Bar แบบ Multi-Threaded"""
    
    def __init__(self, title="StorePOS", subtitle="กำลังเริ่มระบบ..."):
        self.root = ctk.CTk()
        self.title_text = title
        self.subtitle_text = subtitle
        
        # ตั้งค่าหน้าต่างแบบไม่มีกรอบ (Frameless Window)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # ขนาดหน้าต่าง
        width = 520
        height = 300
        
        # คำนวณตำแหน่งให้อยู่ตรงกลางหน้าจอ
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # ตั้งไอคอนถ้ามี
        try:
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)
            else:
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass
            
        # สร้าง Frame หลักในธีมเข้มหรูหรา
        self.main_frame = ctk.CTkFrame(
            self.root,
            corner_radius=16,
            fg_color="#1E1E2E",
            border_width=2,
            border_color="#00ADB5"
        )
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # ปุ่มปิด [✕] มุมขวาบน (เพื่อให้ผู้ใช้สามารถกดปิดได้เสมอ)
        self.btn_close = ctk.CTkButton(
            self.main_frame,
            text="✕",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color="#E53935",
            text_color="#A0A0B0",
            font=("Arial", 14, "bold"),
            command=self.force_exit
        )
        self.btn_close.place(relx=0.96, rely=0.08, anchor="center")

        # ผูกปุ่ม Escape สำหรับสั่งกดปิด Splash Screen
        self.root.bind("<Escape>", lambda e: self.force_exit())

        # หัวข้อโปรแกรม
        self.lbl_title = ctk.CTkLabel(
            self.main_frame,
            text=self.title_text,
            font=("Sarabun", 28, "bold"),
            text_color="#FFFFFF"
        )
        self.lbl_title.pack(pady=(40, 5))

        
        # คำบรรยายใต้หัวข้อ
        self.lbl_subtitle = ctk.CTkLabel(
            self.main_frame,
            text=self.subtitle_text,
            font=("Sarabun", 14),
            text_color="#A0A0B0"
        )
        self.lbl_subtitle.pack(pady=(0, 25))
        
        # หลอด Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            width=420,
            height=14,
            corner_radius=7,
            progress_color="#00ADB5",
            fg_color="#323246"
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0.0)
        
        # Frame แสดงข้อความสถานะและเปอร์เซ็นต์
        self.info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=50, pady=(5, 10))
        
        self.lbl_status = ctk.CTkLabel(
            self.info_frame,
            text="กำลังเริ่มโหลดโปรแกรม...",
            font=("Sarabun", 13),
            text_color="#E0E0E0",
            anchor="w"
        )
        self.lbl_status.pack(side="left")
        
        self.lbl_percent = ctk.CTkLabel(
            self.info_frame,
            text="0%",
            font=("Sarabun", 13, "bold"),
            text_color="#00ADB5",
            anchor="e"
        )
        self.lbl_percent.pack(side="right")
        
        # Footer
        ctk.CTkLabel(
            self.main_frame,
            text="Point of Sale System • Powered by StorePOS",
            font=("Sarabun", 11),
            text_color="#6C7293"
        ).pack(side="bottom", pady=15)
        
        # คิวสำหรับสื่อสารระหว่าง Worker Thread กับ Main GUI Thread
        self.msg_queue = queue.Queue()
        self.on_complete_callback = None
        self.task_results = {}
        self.is_running = True
        
        self.root.update()

    def update_progress(self, val: float, status_text: str = None):
        """อัปเดตเปอร์เซ็นต์ (0.0 ถึง 1.0) และข้อความสถานะ"""
        val = min(max(val, 0.0), 1.0)
        self.progress_bar.set(val)
        percent_int = int(val * 100)
        self.lbl_percent.configure(text=f"{percent_int}%")
        
        if status_text:
            self.lbl_status.configure(text=status_text)
            
        self.root.update_idletasks()

    def run_tasks_threaded(self, task_list, on_complete):
        """
        รันรายการงานหนักใน Background Thread เพื่อไม่ให้ Main UI ค้าง
        
        task_list: รายการของ tuple (name, text, callable_func)
        on_complete: ฟังก์ชันที่จะเรียกบน Main Thread เมื่อทุกงานเสร็จสิ้น
        """
        self.on_complete_callback = on_complete
        
        # เริ่ม Background Worker Thread
        thread = threading.Thread(
            target=self._worker_thread,
            args=(task_list,),
            daemon=True
        )
        thread.start()
        
        # เริ่มลูปเช็ค Queue บน Main Thread
        self.root.after(20, self._check_queue)
        self.root.mainloop()

    def _worker_thread(self, task_list):
        """Worker Thread ทำงานในพื้นหลัง"""
        total_tasks = len(task_list)
        
        for idx, (task_key, status_text, func) in enumerate(task_list, start=1):
            target_progress = idx / total_tasks
            
            # ส่งสถานะเริ่มต้นงาน
            self.msg_queue.put(('progress', target_progress * 0.9, status_text, None))
            
            result = None
            try:
                if callable(func):
                    result = func()
            except Exception as e:
                print(f"Error in splash task {task_key}: {e}")
                result = e
                
            self.task_results[task_key] = result
            
            # ส่งสถานะเสร็จสิ้นงาน
            self.msg_queue.put(('progress', target_progress, status_text, None))
            time.sleep(0.05)
            
        # ส่งสัญญาณว่าทำงานครบทุกอย่างแล้ว
        self.msg_queue.put(('complete', 1.0, "พร้อมใช้งาน!", self.task_results))

    def _check_queue(self):
        """เช็คข้อความจาก Worker Thread บน Main Thread"""
        try:
            while not self.msg_queue.empty():
                msg_type, progress, text, payload = self.msg_queue.get_nowait()
                
                if msg_type == 'progress':
                    self.update_progress(progress, text)
                elif msg_type == 'complete':
                    self.update_progress(1.0, text)
                    self.root.after(100, lambda: self._finish(payload))
                    return
        except Exception:
            pass
            
        if self.is_running:
            self.root.after(20, self._check_queue)

    def _finish(self, results):
        """เสร็จสิ้นกระบวนการ ปิด Splash และเรียก Callback"""
        self.is_running = False
        try:
            self.root.destroy()
        except Exception:
            pass
            
        if callable(self.on_complete_callback):
            self.on_complete_callback(results)

    def force_exit(self):
        """ผู้ใช้กดปิด Splash Screen"""
        self.is_running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def close(self):
        """ปิดหน้าต่าง Splash Screen"""
        self.is_running = False
        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    splash = SplashScreen("StorePOS - 30-Day Trial", "เวอร์ชันทดลองใช้งานฟรี 30 วัน")
    
    demo_tasks = [
        ("dirs", "กำลังตรวจสอบโครงสร้างโฟลเดอร์...", lambda: time.sleep(0.3)),
        ("font", "กำลังลงทะเบียนฟอนต์ภาษาไทย...", lambda: time.sleep(0.3)),
        ("lic", "กำลังตรวจสอบสิทธิ์การใช้งาน...", lambda: time.sleep(0.4)),
        ("db", "กำลังเตรียมฐานข้อมูล...", lambda: time.sleep(0.4)),
    ]
    
    def on_done(res):
        print("Threaded loading complete!", res)
        
    splash.run_tasks_threaded(demo_tasks, on_done)
