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
        _ENGLISH_LAYOUT = _user32.LoadKeyboardLayoutW("00000409", 1)

        def _get_current_layout(hwnd=None):
            """ดึง keyboard layout ปัจจุบันของ thread ที่ใช้งาน"""
            if hwnd:
                thread_id = _user32.GetWindowThreadProcessId(hwnd, None)
                return _user32.GetKeyboardLayout(thread_id)
            return _user32.GetKeyboardLayout(0)

        def _set_english_layout(hwnd=None):
            """สลับ keyboard layout ไปเป็น EN-US ทันที"""
            if _ENGLISH_LAYOUT:
                _user32.ActivateKeyboardLayout(_ENGLISH_LAYOUT, 1)
                if hwnd:
                    _user32.PostMessageW(hwnd, 0x0050, 0, _ENGLISH_LAYOUT)  # WM_INPUTLANGCHANGEREQUEST

        def _set_layout(hwnd, layout):
            """สลับ keyboard layout ไปเป็น layout ที่กำหนด"""
            if layout:
                _user32.ActivateKeyboardLayout(layout, 1)
                if hwnd:
                    _user32.PostMessageW(hwnd, 0x0050, 0, layout)

        _CTYPES_AVAILABLE = True
    except Exception as e:
        _CTYPES_AVAILABLE = False
else:
    _CTYPES_AVAILABLE = False


def bind_english_input(widget, allow_thai=False):
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
        """ตอน focus เข้าช่องบาร์โค้ด → สลับภาษาเป็น EN ทันที"""
        try:
            if _CTYPES_AVAILABLE:
                hwnd = widget.winfo_id()
                try:
                    toplevel = widget.winfo_toplevel()
                    top_hwnd = toplevel.winfo_id()
                except Exception:
                    top_hwnd = hwnd
                
                _prev_layout[0] = _get_current_layout(hwnd)
                _set_english_layout(hwnd)
                if top_hwnd != hwnd:
                    _set_english_layout(top_hwnd)
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
    if not allow_thai:
        widget.bind("<KeyPress>", on_key_press, add="+")


def translate_thai_barcode(text):
    """
    แปลงตัวอักษรภาษาไทยที่เกิดจากการสแกนบาร์โค้ดใน Layout ภาษาไทย
    กลับไปเป็นตัวเลขบาร์โค้ดภาษาอังกฤษมาตรฐาน (Kedmanee Layout Mapping)
    """
    if not text:
        return text

    # แผนผังแป้นพิมพ์ภาษาไทย (Kedmanee) -> ตัวเลขและสัญลักษณ์ในแป้นภาษาอังกฤษ
    mapping = {
        'ๅ': '1', '/': '2', '-': '3', '_': '3', 'ภ': '4', 'ถ': '5',
        'ุ': '6', 'ึ': '7', 'ค': '8', 'ต': '9', 'จ': '0',
        'ข': '-', 'ช': '=',
        # ตัวเลขไทย
        '๑': '1', '๒': '2', '๓': '3', '๔': '4', '๕': '5',
        '๖': '6', '๗': '7', '๘': '8', '๙': '9', '๐': '0',
        # แถบ Shift บนแถวตัวเลข
        '+': '2', 'ู': '5', '฿': '6', '๕': '7', '็': '8', 'ํ': '9', '๊': '0'
    }

    translated = []
    has_thai_digits = False
    for char in text:
        if char in mapping:
            translated.append(mapping[char])
            has_thai_digits = True
        else:
            translated.append(char)

    translated_str = "".join(translated)

    # หากมีการแปลงและผลลัพธ์ที่ได้เป็นตัวเลขและเครื่องหมายขีดล้วนๆ และความยาวเหมาะสมสำหรับบาร์โค้ด (>= 8 ตัวอักษร)
    clean_check = translated_str.replace("-", "")
    if has_thai_digits and clean_check.isdigit() and len(translated_str) >= 8:
        return translated_str

    return text

