# -*- coding: utf-8 -*-
"""
เครื่องมือจัดการรูปภาพ (Image Utilities)
"""

from PIL import Image
import os
from pathlib import Path
from config import IMAGE_OPTIMIZATION

def optimize_image(input_path, output_path=None):
    """
    ปรับปรุงขนาดและคุณภาพของรูปภาพให้เหมาะสมกับโปรแกรม
    """
    try:
        # โหลดรูปภาพ
        img = Image.open(input_path)
        
        # แปลงเป็น RGB ถ้าเป็น RGBA (สำหรับ JPEG)
        if img.mode in ('RGBA', 'P') and IMAGE_OPTIMIZATION.get("format") == "JPEG":
            img = img.convert('RGB')
        
        # ขนาดสูงสุดที่อนุญาต
        max_size = IMAGE_OPTIMIZATION.get("max_image_size", (800, 800))
        
        # ปรับขนาดโดยรักษาอัตราส่วน (Maintain Aspect Ratio)
        # thumbnail จะไม่ขยายรูปถ้าเล็กกว่า max_size อยู่แล้ว
        resample_method = Image.Resampling.BILINEAR if IMAGE_OPTIMIZATION.get("resample_method") == "BILINEAR" else Image.Resampling.LANCZOS
        img.thumbnail(max_size, resample_method)
        
        # ถ้าไม่มี output_path ให้ทับไฟล์เดิม (ระวัง!)
        if not output_path:
            output_path = input_path
            
        # บันทึกรูปภาพ
        img.save(
            output_path, 
            format=IMAGE_OPTIMIZATION.get("format", "JPEG"), 
            quality=IMAGE_OPTIMIZATION.get("quality", 75),
            optimize=True
        )
        return True, output_path
    except Exception as e:
        return False, str(e)

def create_thumbnail(input_path, output_path, size=None):
    """
    สร้างรูปภาพขนาดเล็ก (Thumbnail)
    """
    try:
        if not size:
            size = IMAGE_OPTIMIZATION.get("thumbnail_size", (50, 50))
            
        img = Image.open(input_path)
        img.thumbnail(size, Image.Resampling.BILINEAR)
        img.save(output_path, quality=60)
        return True, output_path
    except Exception as e:
        return False, str(e)
