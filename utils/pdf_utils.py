# -*- coding: utf-8 -*-
"""
ฟังก์ชันสำหรับสร้าง PDF (ใบเสร็จ, รายงาน)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from pathlib import Path


def register_thai_font():
    """ลงทะเบียนฟอนต์ภาษาไทย (FC Sara Samkan)"""
    registered = False
    
    # Path to font file (relative to this file: utils/pdf_utils.py -> project_root/font.ttf)
    base_dir = Path(__file__).resolve().parent.parent
    font_path = base_dir / "FC Sara Samkan [Non-commercial] Bold.ttf"
    
    if not font_path.exists():
        # Fallback to checking specific Windows fonts if project font missing
        print(f"Project font not found at {font_path}, checking system...")
        font_configs = [
            ('THSarabun', 'C:/Windows/Fonts/THSarabunNew.ttf'),
            ('THSarabunBold', 'C:/Windows/Fonts/THSarabunNew Bold.ttf'),
        ]
    else:
        # Use the project font for both normal and bold (since we only have bold)
        font_configs = [
            ('THSarabun', str(font_path)),
            ('THSarabunBold', str(font_path)), 
        ]

    for font_name, f_path in font_configs:
        if Path(f_path).exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, f_path))
                registered = True
            except Exception as e:
                print(f"Failed to register {font_name}: {e}")
                pass
    return registered


def create_receipt_pdf(receipt_data, filename=None, paper_size="A4"):
    """
    สร้างใบเสร็จ PDF รองรับหลายขนาด
    paper_size: "A4", "80mm", "100x150mm"
    """
    receipts_dir = Path("data/receipts")
    receipts_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        sale_number = receipt_data.get('sale_number', 'RECEIPT')
        filename = receipts_dir / f"receipt_{sale_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    else:
        # แก้ไข: ถ้า filename เป็น path มาอยู่แล้ว ไม่ต้องไปบวก receipts_dir ซ้ำ
        filename = Path(filename)
        if not filename.is_absolute() and "data" not in str(filename):
            filename = receipts_dir / filename
    
    # ตรวจสอบว่ามีโฟลเดอร์ปลายทางจริงไหม
    if filename.parent:
        filename.parent.mkdir(parents=True, exist_ok=True)
    
    register_thai_font()
    
    try:
        # กำหนดขนาดกระดาษและระยะขอบ
        if paper_size == "58mm":
            # เครื่องพิมพ์สลิปขนาดเล็ก
            item_count = len(receipt_data.get('items', []))
            estimated_height = 80 + (item_count * 5) + 60
            page_dim = (58*mm, estimated_height*mm)
            margin = 1*mm
            font_size_normal = 8
            font_size_title = 11
        elif paper_size == "80mm":
            # เครื่องพิมพ์สลิปมาตรฐาน
            item_count = len(receipt_data.get('items', []))
            estimated_height = 80 + (item_count * 5) + 60
            page_dim = (80*mm, estimated_height*mm)
            margin = 2*mm
            font_size_normal = 10
            font_size_title = 14
        elif paper_size == "100x150mm":
            page_dim = (100*mm, 150*mm)
            margin = 5*mm
            font_size_normal = 11
            font_size_title = 16
        elif paper_size == "A5":
            page_dim = (148*mm, 210*mm)
            margin = 10*mm
            font_size_normal = 12
            font_size_title = 16
        else:  # Default A4
            page_dim = A4
            margin = 20*mm
            font_size_normal = 14
            font_size_title = 20

        doc = SimpleDocTemplate(
            str(filename),
            pagesize=page_dim,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=margin,
            bottomMargin=margin
        )
        
        styles = getSampleStyleSheet()
        
        # Style แบบเรียบง่าย ไม่มีพื้นหลัง
        normal_style = ParagraphStyle(
            'ThaiNormal',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=font_size_normal,
            leading=font_size_normal * 1.2,
            alignment=TA_CENTER
        )

        left_style = ParagraphStyle(
            'ThaiLeft',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=font_size_normal,
            leading=font_size_normal * 1.2,
            alignment=0 # LEFT
        )
        
        title_style = ParagraphStyle(
            'ThaiTitle',
            parent=styles['Normal'],
            fontName='THSarabunBold',
            fontSize=font_size_title,
            leading=font_size_title * 1.2,
            alignment=TA_CENTER
        )
        
        story = []
        
        company_info = receipt_data.get('company', {})
        
        # 1. ชื่อร้าน
        story.append(Paragraph(company_info.get('name', 'ชื่อร้านค้า'), title_style))
        
        # 2. ที่อยู่ (ตัดให้สั้นถ้าเป็นกระดาษเล็ก)
        address = company_info.get('address', 'ที่อยู่')
        if paper_size == "80mm" and len(address) > 50:
             address = address[:47] + "..."
        story.append(Paragraph(address, normal_style))
        
        story.append(Spacer(1, 2*mm))
        
        # 3. เลขที่ใบเสร็จ + วันเวลา
        sale_date = receipt_data.get('sale_date', '-')
        # พยายามแยกเวลาออกมา (ถ้า format ตรง)
        try:
             dt = datetime.strptime(sale_date, "%d/%m/%Y %H:%M:%S")
             time_str = dt.strftime("%H:%M")
             date_str = dt.strftime("%d/%m/%Y")
        except:
             time_str = ""
             date_str = sale_date

        story.append(Paragraph(f"เลขที่: {receipt_data.get('sale_number', '-')}", left_style))
        story.append(Paragraph(f"วันที่: {date_str} {time_str}", left_style))
        
        story.append(Paragraph("-" * 40, normal_style))
        
        # 4. รายการสินค้า (loop สร้าง paragraph แทน table เพื่อความ simple)
        # item_line_format: "ProductQty x Price     Total"
        
        for item in receipt_data.get('items', []):
            p_name = item.get('product_name', '-')
            qty = item.get('quantity', 0)
            price = item.get('unit_price', 0)
            total = item.get('total_price', 0)
            
            # บรรทัดชื่อสินค้า
            story.append(Paragraph(p_name, left_style))
            
            # บรรทัดรายละเอียด:  2 x 100.00         200.00
            # ใช้ Table แบบไม่มีเส้นเพื่อจัดหน้าให้สวย
            detail_data = [[f"   {qty} x {price:,.2f}", f"{total:,.2f}"]]
            t = Table(detail_data, colWidths=[None, 20*mm if paper_size == "80mm" else 40*mm])
            t.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'THSarabun', font_size_normal),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Qty x Price ชิดซ้าย
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'), # Total ชิดขวา
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t)
            
        story.append(Paragraph("-" * 40, normal_style))
        
        # 5. สรุปยอด (Table)
        # ยอดรวม
        # รับเงิน
        # เงินทอน
        
        summary_data = [
            ['ยอดรวม', f"{receipt_data.get('total_amount', 0):,.2f}"],
            ['รับเงิน', f"{receipt_data.get('paid_amount', 0):,.2f}"],
            ['เงินทอน', f"{receipt_data.get('change_amount', 0):,.2f}"]
        ]
        
        sum_table = Table(summary_data, colWidths=[None, 25*mm if paper_size == "80mm" else 40*mm])
        sum_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'THSarabun', font_size_normal),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (1, 0), 'THSarabunBold'), # ยอดรวมตัวหนา
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))
        story.append(sum_table)
        
        story.append(Paragraph("-" * 40, normal_style))
        
        # 5.5 Barcode (ถ้าเปิดใช้งาน)
        show_barcode = True
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            barcode_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'receipt_show_barcode'")
            db.disconnect()
            if barcode_setting:
                show_barcode = barcode_setting['setting_value'] == 'True'
        except Exception:
            pass

        if show_barcode:
            try:
                from reportlab.graphics.barcodes import code128
                barcode_val = receipt_data.get('sale_number', '')
                if barcode_val:
                    barcode_flowable = code128.Code128(barcode_val, barHeight=10*mm, barWidth=0.5*mm)
                    # ใส่ใน Table เพื่อจัดให้อยู่กึ่งกลาง
                    t_barcode = Table([[barcode_flowable]])
                    t_barcode.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
                    ]))
                    story.append(t_barcode)
                    story.append(Paragraph(barcode_val, normal_style))
                    story.append(Paragraph("-" * 40, normal_style))
            except Exception as e:
                print(f"Error rendering PDF barcode: {e}")
        
        # 6. Footer message
        story.append(Paragraph("ขอบคุณที่ใช้บริการ", normal_style))
        
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error creating PDF receipt: {e}")
        return False


def export_sales_report(sales_data, filename):
    """Export รายงานยอดขาย (ไม่ใช้แล้ว - ใช้ Excel แทน)"""
    pass
