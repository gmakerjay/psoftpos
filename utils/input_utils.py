# -*- coding: utf-8 -*-
"""
input_utils.py — ฟังก์ชันช่วยจัดการ keyboard input
รองรับปืนบาร์โค้ดทุกรุ่น โดยบังคับช่องบาร์โค้ดให้รับ input เป็น EN เสมอ
"""

import sys
import platform


def _is_windows():
    return platform.system() == "Windows"


# ============================================================
# Windows IME / Keyboard Layout Control
# ============================================================
if _is_windows():
    try:
        import ctypes
        import ctypes.wintypes

        _user32 = ctypes.windll.user32
        _ENGLISH_LAYOUT = ctypes.windll.kernel32.LoadKeyboardLayoutW("00000409", 1)

        def _get_current_layout(hwnd):
            """ดึง keyboard layout ปัจจุบันของ thread ที่ใช้งาน"""
            thread_id = _user32.GetWindowThreadProcessId(hwnd, None)
            return _user32.GetKeyboardLayout(thread_id)

        def _set_english_layout(hwnd):
            """สลับ keyboard layout ไปเป็น EN-US"""
            _user32.PostMessageW(hwnd, 0x0050, 0, _ENGLISH_LAYOUT)  # WM_INPUTLANGCHANGEREQUEST

        def _set_layout(hwnd, layout):
            """สลับ keyboard layout ไปเป็น layout ที่กำหนด"""
            _user32.PostMessageW(hwnd, 0x0050, 0, layout)

        _CTYPES_AVAILABLE = True
    except Exception:
        _CTYPES_AVAILABLE = False
else:
    _CTYPES_AVAILABLE = False


def bind_english_input(widget):
    """
    ผูก event กับ widget เพื่อบังคับให้รับ input เป็น EN เมื่อ focus
    รองรับปืนบาร์โค้ดทุกรุ่น — ทำงานบน Windows เท่านั้น

    วิธีใช้:
        bind_english_input(self.barcode_entry)
    """
    if not _is_windows():
        return  # ไม่ทำอะไรบน macOS/Linux

    # เก็บ layout เดิมไว้คืนค่าตอน FocusOut
    _prev_layout = [None]

    def on_focus_in(event):
        """ตอน focus เข้าช่องบาร์โค้ด → สลับเป็น EN"""
        try:
            if _CTYPES_AVAILABLE:
                hwnd = widget.winfo_id()
                _prev_layout[0] = _get_current_layout(hwnd)
                _set_english_layout(hwnd)
        except Exception:
            pass

        # วิธีสำรอง: บังคับผ่าน IME disable (รองรับปืนราคาถูก)
        try:
            widget.configure(inputmode="none")  # ปิด on-screen keyboard (mobile)
        except Exception:
            pass

    def on_focus_out(event):
        """ตอน focus ออก → คืน layout เดิม"""
        try:
            if _CTYPES_AVAILABLE and _prev_layout[0]:
                hwnd = widget.winfo_id()
                _set_layout(hwnd, _prev_layout[0])
        except Exception:
            pass

    def on_key_press(event):
        """
        กรอง input ที่ไม่ใช่ ASCII ออก — รองรับปืนราคาถูกที่ส่งอักขระแปลก
        บาร์โค้ดมาตรฐานมีแค่ตัวเลข 0-9 และตัวอักษร A-Z a-z - . /
        """
        char = event.char
        if char and ord(char) > 127:
            # ตัดอักขระที่ไม่ใช่ ASCII (เช่น ภาษาไทย) ออก
            return "break"

    widget.bind("<FocusIn>", on_focus_in, add="+")
    widget.bind("<FocusOut>", on_focus_out, add="+")
    widget.bind("<KeyPress>", on_key_press, add="+")
