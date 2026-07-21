# -*- coding: utf-8 -*-
"""
ทดสอบพิมพ์ภาษาไทยบน XP-58 ด้วย codepage ต่างๆ
เพื่อหาค่าที่ถูกต้องสำหรับเครื่องนี้
"""

import win32print
import sys

PRINTER_NAME = "XP-58"

# ข้อความทดสอบภาษาไทย
THAI_TEST = "ทดสอบภาษาไทย"

ESC = b'\x1b'
GS = b'\x1d'
FS = b'\x1c'

def send_raw(data):
    """ส่งข้อมูลดิบไปเครื่องพิมพ์"""
    hPrinter = win32print.OpenPrinter(PRINTER_NAME)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Thai_Test", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)

def test_codepage(cp_num, label, use_fs_c=True):
    """ทดสอบ codepage หนึ่งค่า"""
    commands = []
    
    # Reset
    commands.append(ESC + b'@')
    
    # Cancel Chinese mode
    commands.append(FS + b'.')
    
    # Set codepage
    commands.append(ESC + b't' + bytes([cp_num]))
    
    # Thai mode (FS C 0x01) — บางเครื่องต้องใช้ บางเครื่องไม่
    if use_fs_c:
        commands.append(FS + b'C\x01')
    
    # International character set USA
    commands.append(ESC + b'R\x00')
    
    # พิมพ์หัวข้อ
    header = f"=== CP {cp_num} ({label}) FS.C={'ON' if use_fs_c else 'OFF'} ===\n"
    commands.append(header.encode('ascii', errors='ignore'))
    
    # พิมพ์ภาษาไทย
    commands.append(THAI_TEST.encode('cp874', errors='ignore') + b'\n')
    commands.append("ชื่อร้านค้า".encode('cp874', errors='ignore') + b'\n')
    commands.append("เลขที่: SL001".encode('cp874', errors='ignore') + b'\n')
    commands.append("ยอดสุทธิ:".encode('cp874', errors='ignore') + b'\n')
    commands.append("รับเงิน:".encode('cp874', errors='ignore') + b'\n')
    commands.append("เงินทอน:".encode('cp874', errors='ignore') + b'\n')
    
    # Line feed
    commands.append(b'\n')
    
    return b''.join(commands)


# สร้างชุดทดสอบทั้งหมด
all_commands = []

# ทดสอบ codepage ที่น่าจะใช้ได้กับเครื่องจีน
test_configs = [
    (18,  "CP18-Xprinter",    True),
    (18,  "CP18-NoFSC",       False),
    (255, "CP255-Import",     True),
    (255, "CP255-NoFSC",      False),
    (254, "CP254-OEM-CN",     True),
    (254, "CP254-NoFSC",      False),
    (252, "CP252-OEM-TH",     True),
    (252, "CP252-NoFSC",      False),
    (26,  "CP26-Epson",       False),  # Epson ไม่ใช้ FS C
    (30,  "CP30-Star",        False),  # Star ไม่ใช้ FS C
    (0,   "CP0-Default",      True),
    (0,   "CP0-NoFSC",        False),
    (11,  "CP11-TIS620",      True),
    (11,  "CP11-NoFSC",       False),
    (1,   "CP1-Default1",     True),
    (1,   "CP1-NoFSC",        False),
]

for cp, label, fs_c in test_configs:
    all_commands.append(test_codepage(cp, label, fs_c))

# ตัดกระดาษตอนจบ
all_commands.append(b'\n\n\n')
all_commands.append(GS + b'V\x00')

final_data = b''.join(all_commands)
print(f"Sending {len(final_data)} bytes to {PRINTER_NAME}...")
print(f"Testing {len(test_configs)} codepage configurations")

send_raw(final_data)
print("Done! Check the printout to find which codepage shows Thai correctly.")
