# -*- coding: utf-8 -*-
"""
A4 30 Barcode Labels PDF to PNG Converter
สร้าง PDF บาร์โค้ด 30 ดวง และแปลงหน้าแรกเป็นภาพ PNG เพื่อตรวจดูลายเส้นบาร์โค้ด
"""
import sys
from pathlib import Path
import os
import fitz  # PyMuPDF

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.pdf_utils import create_barcode_labels_pdf

def convert_pdf_to_png():
    print("=== ขั้นที่ 1: สร้างไฟล์ PDF บาร์โค้ด 30 ดวงบน A4 ===")
    print_items = [
        {
            'product_name': 'กาแฟปรุงสำเร็จ ตรานกแก้ว คั่วกลางรสเข้มข้นกลิ่นหอม',
            'barcode': '885012345678',
            'retail_price': 25.00,
            'quantity': 30  # พิมพ์ 30 ช่องป้าย
        }
    ]
    
    pdf_path = Path("data/test_30_barcode_labels_A4.pdf")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    # สร้าง PDF
    success = create_barcode_labels_pdf(
        print_items, 
        str(pdf_path), 
        cols=3, 
        rows=10, 
        show_name=True, 
        show_price=True, 
        show_code=True
    )
    
    if not success or not pdf_path.exists():
        print("[ERROR] ไม่สามารถสร้างไฟล์ PDF ได้")
        return
        
    print("=== ขั้นที่ 2: แปลง PDF หน้าแรกเป็นรูปภาพ PNG ===")
    png_path = Path("data/test_30_barcode_labels_A4.png")
    
    # ใช้ fitz เปิด PDF และเรนเดอร์เป็นภาพ PNG ความละเอียด 150 DPI
    doc = fitz.open(str(pdf_path))
    page = doc.load_page(0)  # หน้าแรก (หน้า 0)
    
    zoom = 2.0  # ซูม 2 เท่าเพื่อให้ภาพคมชัด (150 DPI)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    pix.save(str(png_path))
    doc.close()
    
    print(f"  [SUCCESS] แปลงไฟล์รูปสำเร็จที่: {png_path.resolve()} ({png_path.stat().st_size} bytes)")
    
    # เปิดภาพบนหน้าจอทันที
    os.startfile(str(png_path.resolve()))
    print("  [INFO] สั่งเปิดรูปภาพบนหน้าจอเรียบร้อยแล้ว!")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    convert_pdf_to_png()
