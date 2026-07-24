# -*- coding: utf-8 -*-
"""
ระบบจัดการทรัพยากรและรีสตาร์ทแอปพลิเคชัน (System Utilities)
"""

import sys
import os

def cleanup_resources():
    """ทำความสะอาดคืนทรัพยากร ปิดการเชื่อมต่อฐานข้อมูล ปิดไฟล์ Log ยกเลิกฟอนต์ และคืน Working Directory"""
    try:
        from database.db_manager import DatabaseManager
        DatabaseManager.close_all_connections()
    except Exception:
        pass
        
    try:
        import platform
        if platform.system() == 'Windows':
            import ctypes
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            font_path = os.path.join(base_path, "FC Sara Samkan [Non-commercial] Bold.ttf")
            if os.path.exists(font_path):
                ctypes.windll.gdi32.RemoveFontResourceW(font_path)
    except Exception:
        pass
        
    try:
        import logging
        logging.shutdown()
    except Exception:
        pass
        
    try:
        os.chdir(os.path.expanduser("~"))
    except Exception:
        pass

def restart_application():
    """ทำความสะอาดทรัพยากรทั้งหมดแล้วสั่งรีสตาร์ทเปิดโปรแกรมใหม่ทันที"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        executable = sys.executable
        args = sys.argv
    else:
        # หา directory ที่มี main.py
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        executable = sys.executable
        args = sys.argv
        
    cleanup_resources()
    try:
        os.chdir(base_path)
    except Exception:
        pass
    os.execl(executable, executable, *args)
