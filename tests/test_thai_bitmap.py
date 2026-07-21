# -*- coding: utf-8 -*-
"""
ทดสอบพิมพ์ภาษาไทยแบบ Bitmap (Raster Image) บน XP-58 (copy 1)
วิธีนี้ render ข้อความเป็นรูปภาพก่อน แล้วส่งเป็น dot pattern → ไม่ต้องพึ่ง Thai font ROM
"""

import win32print
from PIL import Image, ImageDraw, ImageFont
import struct

PRINTER_NAME = "XP-58 (copy 1)"
PAPER_WIDTH_DOTS = 384  # 58mm printer = 384 dots (203 DPI)

def text_to_image(lines, font_path, font_size=20, bold_lines=None):
    """แปลงข้อความหลายบรรทัดเป็นรูปภาพขาวดำ"""
    if bold_lines is None:
        bold_lines = set()
    
    font = ImageFont.truetype(font_path, font_size)
    font_bold = ImageFont.truetype(font_path, font_size + 4)
    
    # คำนวณความสูงรวม
    line_height = font_size + 8
    bold_line_height = font_size + 12
    total_height = 0
    for i, line in enumerate(lines):
        total_height += bold_line_height if i in bold_lines else line_height
    total_height += 20  # padding
    
    # สร้างภาพขาวดำ
    img = Image.new('1', (PAPER_WIDTH_DOTS, total_height), 1)  # 1 = white
    draw = ImageDraw.Draw(img)
    
    y = 10
    for i, line in enumerate(lines):
        is_bold = i in bold_lines
        f = font_bold if is_bold else font
        
        if line.startswith('[CENTER]'):
            text = line.replace('[CENTER]', '')
            bbox = f.getbbox(text)
            text_width = bbox[2] - bbox[0]
            x = (PAPER_WIDTH_DOTS - text_width) // 2
        elif line.startswith('[RIGHT]'):
            text = line.replace('[RIGHT]', '')
            bbox = f.getbbox(text)
            text_width = bbox[2] - bbox[0]
            x = PAPER_WIDTH_DOTS - text_width - 5
        elif '\t' in line:
            # ซ้าย-ขวา (ใช้ tab คั่น)
            parts = line.split('\t')
            draw.text((5, y), parts[0], font=f, fill=0)
            if len(parts) > 1:
                bbox = f.getbbox(parts[1])
                rw = bbox[2] - bbox[0]
                draw.text((PAPER_WIDTH_DOTS - rw - 5, y), parts[1], font=f, fill=0)
            y += bold_line_height if is_bold else line_height
            continue
        else:
            text = line
            x = 5
        
        draw.text((x, y), text, font=f, fill=0)
        y += bold_line_height if is_bold else line_height
    
    return img


def image_to_escpos_raster(img):
    """แปลง PIL Image เป็นคำสั่ง ESC/POS raster (GS v 0)"""
    # Ensure 1-bit
    img = img.convert('1')
    width, height = img.size
    
    # ความกว้างเป็น bytes (8 pixels per byte)
    width_bytes = (width + 7) // 8
    
    commands = bytearray()
    
    # GS v 0 — Print raster bit image
    # GS v 0 m xL xH yL yH d1...dk
    # m = 0 (normal), 1 (double-width), 2 (double-height), 3 (quadruple)
    m = 0
    xL = width_bytes & 0xFF
    xH = (width_bytes >> 8) & 0xFF
    yL = height & 0xFF
    yH = (height >> 8) & 0xFF
    
    commands += b'\x1d\x76\x30'  # GS v 0
    commands += bytes([m, xL, xH, yL, yH])
    
    pixels = img.load()
    for row in range(height):
        row_data = bytearray(width_bytes)
        for col in range(width):
            if pixels[col, row] == 0:  # black pixel
                byte_idx = col // 8
                bit_idx = 7 - (col % 8)
                row_data[byte_idx] |= (1 << bit_idx)
        commands += bytes(row_data)
    
    return bytes(commands)


def send_raw(data):
    """ส่งข้อมูลดิบไปเครื่องพิมพ์"""
    hPrinter = win32print.OpenPrinter(PRINTER_NAME)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Thai_Bitmap_Test", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)


# === สร้างใบเสร็จทดสอบ ===
font_path = "FC Sara Samkan [Non-commercial] Bold.ttf"

lines = [
    "[CENTER]ร้านค้าทดสอบ",
    "[CENTER]Test Store",
    "--------------------------------",
    "เลขที่: SL202607160001",
    "วันที่: 2026-07-16 16:00:00",
    "พนักงาน: สมชาย ใจดี",
    "--------------------------------",
    "น้ำดื่ม 600ml",
    "  3 x 10\t30",
    "มาม่าต้มยำกุ้ง",
    "  5 x 7\t35",
    "ขนมปังแผ่น (ยาว)",
    "  1 x 35\t35",
    "--------------------------------",
    "ยอดสุทธิ:\t100.00",
    "--------------------------------",
    "รับเงิน:\t100.00",
    "เงินทอน:\t0.00",
    "",
    "[CENTER]ขอบคุณที่ใช้บริการ",
    "[CENTER]ยินดีให้บริการ",
]

bold_lines = {0, 14}  # ชื่อร้านและยอดสุทธิ

print("Rendering Thai text to bitmap...")
img = text_to_image(lines, font_path, font_size=18, bold_lines=bold_lines)
img.save("scratch/receipt_test.png")
print(f"Image size: {img.size}")

print("Converting to ESC/POS raster commands...")
commands = bytearray()
commands += b'\x1b\x40'  # ESC @ — Initialize printer
commands += image_to_escpos_raster(img)
commands += b'\n\n\n'
commands += b'\x1d\x56\x00'  # GS V 0 — Full cut

print(f"Sending {len(commands)} bytes to {PRINTER_NAME}...")
send_raw(bytes(commands))
print("Done! Check the printout!")
