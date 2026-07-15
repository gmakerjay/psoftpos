# -*- coding: utf-8 -*-
"""
ฟังก์ชันสำหรับจัดการบาร์โค้ด
"""

import barcode
from barcode.writer import ImageWriter
from pathlib import Path
from PIL import Image
import io


class BarcodeGenerator:
    """สร้างและจัดการบาร์โค้ด"""
    
    @staticmethod
    def generate_barcode(code, barcode_type='code128', output_path=None):
        """
        สร้างบาร์โค้ด
        
        Args:
            code: รหัสที่ต้องการสร้างเป็นบาร์โค้ด
            barcode_type: ประเภทบาร์โค้ด (code128, ean13, etc.)
            output_path: path สำหรับบันทึกไฟล์ (ถ้าไม่ระบุจะคืนเป็น PIL Image)
            
        Returns:
            PIL Image หรือ path ของไฟล์ที่บันทึก
        """
        try:
            # เลือกประเภทบาร์โค้ด
            if barcode_type.lower() == 'ean13':
                # EAN13 ต้องมี 12 หลัก (เพิ่ม checksum อัตโนมัติ)
                code = str(code).zfill(12)
                barcode_class = barcode.get_barcode_class('ean13')
            else:
                # Code128 รองรับทุกตัวอักษร
                barcode_class = barcode.get_barcode_class('code128')
            
            # สร้างบาร์โค้ด
            if output_path:
                # บันทึกเป็นไฟล์
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                barcode_instance = barcode_class(code, writer=ImageWriter())
                filename = barcode_instance.save(str(output_path.with_suffix('')))
                return filename
            else:
                # คืนเป็น PIL Image
                barcode_instance = barcode_class(code, writer=ImageWriter())
                buffer = io.BytesIO()
                barcode_instance.write(buffer)
                buffer.seek(0)
                return Image.open(buffer)
                
        except Exception as e:
            print(f"Error generating barcode: {e}")
            return None
    
    @staticmethod
    def generate_barcode_number(prefix='', length=12):
        """
        สร้างเลขบาร์โค้ดอัตโนมัติ
        
        Args:
            prefix: คำนำหน้า
            length: ความยาวของตัวเลข
            
        Returns:
            เลขบาร์โค้ด
        """
        import random
        from datetime import datetime
        
        # ใช้เวลาปัจจุบันและเลขสุ่ม
        timestamp = datetime.now().strftime('%y%m%d%H%M%S')
        random_num = random.randint(1000, 9999)
        
        barcode_num = f"{prefix}{timestamp}{random_num}"
        
        # ตัดให้เหลือตามความยาวที่ต้องการ
        if len(barcode_num) > length:
            barcode_num = barcode_num[:length]
        else:
            barcode_num = barcode_num.ljust(length, '0')
            
        return barcode_num
    
    @staticmethod
    def validate_barcode(code, barcode_type='code128'):
        """
        ตรวจสอบความถูกต้องของบาร์โค้ด
        
        Args:
            code: รหัสที่ต้องการตรวจสอบ
            barcode_type: ประเภทบาร์โค้ด
            
        Returns:
            True ถ้าถูกต้อง, False ถ้าไม่ถูกต้อง
        """
        try:
            if barcode_type.lower() == 'ean13':
                # EAN13 ต้องมี 12-13 หลัก
                if not code.isdigit():
                    return False
                if len(code) not in [12, 13]:
                    return False
            elif barcode_type.lower() == 'code128':
                # Code128 รองรับทุกตัวอักษร
                if len(code) == 0:
                    return False
            
            return True
        except:
            return False


# ฟังก์ชันสำหรับใช้งานง่าย
def create_barcode(code, save_path=None, barcode_type='code128'):
    """สร้างบาร์โค้ด (ฟังก์ชันแบบง่าย)"""
    generator = BarcodeGenerator()
    return generator.generate_barcode(code, barcode_type, save_path)


def generate_product_barcode():
    """สร้างเลขบาร์โค้ดสินค้าอัตโนมัติ"""
    generator = BarcodeGenerator()
    return generator.generate_barcode_number(prefix='', length=12)


if __name__ == "__main__":
    # ทดสอบ
    print("ทดสอบการสร้างบาร์โค้ด...")
    
    # สร้างเลขบาร์โค้ด
    barcode_num = generate_product_barcode()
    print(f"เลขบาร์โค้ด: {barcode_num}")
    
    # สร้างภาพบาร์โค้ด
    image = create_barcode(barcode_num)
    if image:
        print("สร้างบาร์โค้ดสำเร็จ!")
        # image.show()  # แสดงภาพ
    else:
        print("สร้างบาร์โค้ดไม่สำเร็จ")
