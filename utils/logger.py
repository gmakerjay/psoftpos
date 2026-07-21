# -*- coding: utf-8 -*-
"""
Logger System - ระบบบันทึก Log สำหรับ Debug และวิเคราะห์ปัญหาของลูกค้า
"""

import os
import logging
import sys
import platform
import threading
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler


class POSLogger:
    """ระบบ Logging สำหรับโปรแกรม POS"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(POSLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not POSLogger._initialized:
            self.setup_logger()
            POSLogger._initialized = True
    
    def setup_logger(self):
        """ตั้งค่า Logger"""
        # ป้องกัน UnicodeEncodeError เมื่อรันบน Windows terminal (CP874/CP1252)
        try:
            sys.stdout.reconfigure(errors='replace')
            sys.stderr.reconfigure(errors='replace')
        except:
            pass
            
        # สร้างโฟลเดอร์ Logs
        os.makedirs("Logs", exist_ok=True)
        
        # สร้างชื่อไฟล์ log ตามวันที่
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = f"Logs/{today}.log"
        
        # สร้าง Logger
        self.logger = logging.getLogger("POS_System")
        self.logger.setLevel(logging.DEBUG)
        
        # ลบ handlers เก่า (ถ้ามี)
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # ===== File Handler (บันทึกลงไฟล์) =====
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=30,  # เก็บไว้ 30 ไฟล์
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Format สำหรับไฟล์ (รายละเอียดลึก: เวลา, ระดับ, ไฟล์:เลขบรรทัด, ข้อความ)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # ===== Console Handler (แสดงบน Terminal) =====
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # บันทึกทุกอย่างลง Console เพื่อการ Debug
        
        # Format สำหรับ Console
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # เพิ่ม Handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # บันทึกข้อมูลสภาพแวดล้อมระบบ (Environment Info) เพื่อความสะดวกในการวิเคราะห์ปัญหาของลูกค้า
        self.logger.info("="*70)
        self.logger.info("POS System Started")
        self.logger.info(f"Date/Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Log File   : {log_file}")
        self.logger.info(f"OS Platform: {platform.platform()} ({platform.architecture()[0]})")
        self.logger.info(f"Python Ver : {sys.version.split()[0]}")
        self.logger.info(f"Exec Path  : {sys.executable}")
        self.logger.info(f"Work Dir   : {os.getcwd()}")
        self.logger.info("="*70)
    
    def get_logger(self):
        """ดึง Logger ไปใช้"""
        return self.logger
    
    def new_session(self, session_type="OPEN"):
        """เริ่ม Session ใหม่ (เมื่อเปิด/ปิดร้าน)"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = f"Logs/{today}.log"
        
        # ถ้าวันเปลี่ยน สร้างไฟล์ใหม่ (ใช้ abspath เพื่อเทียบกับ baseFilename)
        if os.path.abspath(log_file) != self.logger.handlers[0].baseFilename:
            self.setup_logger()
        
        self.logger.info("")
        self.logger.info("-" * 70)
        self.logger.info(f"NEW SESSION: {session_type}")
        self.logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("-" * 70)
        self.logger.info("")
    
    @staticmethod
    def log_exception(exc_type, exc_value, exc_traceback):
        """จับ Exception ทั้งโปรแกรม (ทั้ง Main Thread, GUI Callbacks, และ Background Threads)"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = POSLogger().get_logger()
        logger.critical("UNHANDLED EXCEPTION ENCOUNTERED:", exc_info=(exc_type, exc_value, exc_traceback))


# ===== Global Functions =====

def get_logger(name=None):
    """ดึง Logger ไปใช้ในไฟล์อื่นๆ"""
    pos_logger = POSLogger()
    if name:
        return logging.getLogger(f"POS_System.{name}")
    else:
        return pos_logger.get_logger()


def log_function_call(func):
    """Decorator สำหรับ log การเรียกใช้ function"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling: {func.__name__}({args}, {kwargs})")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}", exc_info=True)
            raise
    return wrapper


def log_database_query(query, params=None):
    """Log Database Query"""
    logger = get_logger("Database")
    if params:
        logger.debug(f"SQL: {query} | Params: {params}")
    else:
        logger.debug(f"SQL: {query}")


def log_user_action(user_id, action, details=""):
    """Log User Action"""
    logger = get_logger("UserAction")
    logger.info(f"User {user_id}: {action} {details}")


def log_sale(sale_id, total, items_count):
    """Log Sale Transaction"""
    logger = get_logger("Sales")
    logger.info(f"Sale #{sale_id}: {items_count} items, Total: {total:,.2f}")


def log_error(message, exc_info=False):
    """Log Error"""
    logger = get_logger("Error")
    logger.error(f"ERROR: {message}", exc_info=exc_info)


def log_warning(message):
    """Log Warning"""
    logger = get_logger("Warning")
    logger.warning(f"WARNING: {message}")


def log_info(message):
    """Log Info"""
    logger = get_logger("Info")
    logger.info(f"INFO: {message}")


def log_debug(message):
    """Log Debug"""
    logger = get_logger("Debug")
    logger.debug(f"DEBUG: {message}")


def new_log_session(session_type="OPEN"):
    """สร้าง Log Session ใหม่"""
    pos_logger = POSLogger()
    pos_logger.new_session(session_type)


def export_logs_zip(output_path=None):
    """ส่งออกไฟล์ Log ทั้งหมดใส่ไฟล์ ZIP เพื่อส่งให้ทีมงานซัพพอร์ตวิเคราะห์ปัญหาได้ง่าย"""
    try:
        os.makedirs("Logs", exist_ok=True)
        if not output_path:
            today = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_path = os.path.abspath(f"Logs/SystemLogs_{today}.zip")
            
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("Logs"):
                for file in files:
                    if file.endswith(".log"):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, "Logs")
                        zipf.write(file_path, arcname)
        return True, output_path
    except Exception as e:
        log_error(f"Failed to export logs zip: {e}", exc_info=True)
        return False, str(e)


# ===== Initialize Logger & Global Hooks =====
_pos_logger = POSLogger()

# 1. ดักจับ Exception จาก Python Main Script
sys.excepthook = POSLogger.log_exception

# 2. ดักจับ Exception จาก Background Threads
def _thread_excepthook(args):
    POSLogger.log_exception(args.exc_type, args.exc_value, args.exc_tb)

if hasattr(threading, 'excepthook'):
    threading.excepthook = _thread_excepthook

# 3. ดักจับ Exception จาก Tkinter GUI Callbacks (ปุ่มกด, Event, Trace)
try:
    import tkinter as tk
    def _tk_excepthook(self, exc_type, exc_value, exc_traceback):
        POSLogger.log_exception(exc_type, exc_value, exc_traceback)
    tk.Tk.report_callback_exception = _tk_excepthook
except Exception as _ex_tk:
    pass


if __name__ == "__main__":
    logger = get_logger(__name__)
    
    logger.debug("This is DEBUG message")
    logger.info("This is INFO message")
    logger.warning("This is WARNING message")
    logger.error("This is ERROR message")
    logger.critical("This is CRITICAL message")
    
    log_user_action(1, "LOGIN", "admin user")
    log_sale(123, 1500.00, 5)
    log_error("Test error message")
    log_warning("Test warning message")
    log_info("Test info message")
    
    try:
        result = 10 / 0
    except Exception as e:
        logger.error("Division by zero", exc_info=True)
    
    new_log_session("TEST_SESSION")
    
    ok, zpath = export_logs_zip()
    print(f"\n✅ Logger tested & exported to: {zpath}")

    logger.debug("This is DEBUG message")
    logger.info("This is INFO message")
    logger.warning("This is WARNING message")
    logger.error("This is ERROR message")
    logger.critical("This is CRITICAL message")
    
    # ทดสอบ log functions
    log_user_action(1, "LOGIN", "admin user")
    log_sale(123, 1500.00, 5)
    log_error("Test error message")
    log_warning("Test warning message")
    log_info("Test info message")
    
    # ทดสอบ exception
    try:
        result = 10 / 0
    except Exception as e:
        logger.error("Division by zero", exc_info=True)
    
    # ทดสอบ new session
    new_log_session("TEST_SESSION")
    
    print("\n✅ Logger tested successfully!")
    print(f"📄 Check log file: Logs/{datetime.now().strftime('%Y-%m-%d')}.log")
