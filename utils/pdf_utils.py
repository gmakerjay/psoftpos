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
        
        cust_name = receipt_data.get('customer_name')
        if cust_name:
            story.append(Paragraph(f"สมาชิก: {cust_name}", left_style))
        
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
                from reportlab.graphics.barcode import code128
                barcode_val = receipt_data.get('sale_number', '')
                if barcode_val:
                    barcode_flowable = code128.Code128(barcode_val, barHeight=5*mm, barWidth=0.25*mm)
                    # ใส่ใน Table เพื่อจัดให้อยู่กึ่งกลาง
                    t_barcode = Table([[barcode_flowable]])
                    t_barcode.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
                    ]))
                    story.append(t_barcode)
                    story.append(Paragraph(barcode_val, normal_style))
                    story.append(Paragraph("-" * 40, normal_style))
            except Exception as e:
                print(f"Error rendering PDF barcode: {e}")
        
        # 6. Footer message
        story.append(Paragraph("ขอบคุณที่ใช้บริการ", normal_style))
        
        # วาดรูป QR Code ท้ายใบเสร็จ PDF
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            qr_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
            db.disconnect()
            if qr_setting and qr_setting['setting_value'].strip():
                qr_path = Path(qr_setting['setting_value'].strip())
                if qr_path.exists():
                    from reportlab.platypus import Image as RLImage
                    # ปรับขนาดตามหน้ากระดาษ
                    if paper_size == "58mm":
                        qr_w = 20 * mm
                        qr_h = 20 * mm
                    elif paper_size == "80mm":
                        qr_w = 30 * mm
                        qr_h = 30 * mm
                    else: # A4 / A5
                        qr_w = 40 * mm
                        qr_h = 40 * mm
                    
                    qr_flowable = RLImage(str(qr_path), width=qr_w, height=qr_h)
                    t_qr = Table([[qr_flowable]])
                    t_qr.setStyle(TableStyle([
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('LEFTPADDING', (0,0), (-1,-1), 0),
                        ('RIGHTPADDING', (0,0), (-1,-1), 0),
                        ('TOPPADDING', (0,0), (-1,-1), 3*mm),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 3*mm),
                    ]))
                    story.append(t_qr)
        except Exception as e:
            print(f"Error rendering PDF QR Code: {e}")
        
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error creating PDF receipt: {e}")
        return False


def export_sales_report(sales_data, filename):
    """Export รายงานยอดขาย (ไม่ใช้แล้ว - ใช้ Excel แทน)"""
    pass


def create_barcode_labels_pdf(print_items, filename, cols=6, rows=18, show_name=True, show_price=True, show_code=True):
    """
    สร้างไฟล์ PDF สำหรับพริ้นบาร์โค้ดสินค้าในแบบตาราง (Grid Labels) ลงในกระดาษ A4
    มาตรฐานเริ่มต้น 6 คอลัมน์ x 18 แถว (ดวงละ 3cm x 1.5cm / 108 ดวงต่อหน้า)
    หรือปรับแถบให้เต็มสัดส่วนขอบไม่เหลือพื้นที่ว่างส่วนเกิน
    """
    register_thai_font()
    
    filename = Path(filename)
    if filename.parent:
        filename.parent.mkdir(parents=True, exist_ok=True)
        
    try:
        import barcode as barcode_lib
        from barcode.writer import ImageWriter
        from io import BytesIO
        from reportlab.platypus import Image as RLImage
        
        # กำหนดขนาดกระดาษ A4 (210 x 297 mm)
        page_w, page_h = A4
        margin = 3 * mm
        printable_w = page_w - (2 * margin)
        printable_h = page_h - (2 * margin)
        
        cell_w = printable_w / cols
        cell_h = printable_h / rows
        
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=margin,
            bottomMargin=margin
        )
        
        styles = getSampleStyleSheet()
        
        # ปรับขนาดฟอนต์ให้สมส่วน ไม่เล็กรวมกันเป็นก้อน
        font_sz = 7.0 if cols >= 6 else 8.5
        leading_sz = 8.0 if cols >= 6 else 9.5
        
        name_style = ParagraphStyle(
            'LabelName',
            parent=styles['Normal'],
            fontName='THSarabunBold',
            fontSize=font_sz,
            leading=leading_sz,
            alignment=1,
            textColor=colors.black
        )
        
        info_style = ParagraphStyle(
            'LabelInfo',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=font_sz,
            leading=leading_sz,
            alignment=1,
            textColor=colors.black
        )
        
        labels = []
        # Cache barcode images per product (สร้างครั้งเดียว ใช้ซ้ำตามจำนวน)
        barcode_cache = {}
        
        for item in print_items:
            name = item.get('product_name', '-')
            code = item.get('barcode', '')
            price = item.get('retail_price', 0)
            qty = int(item.get('quantity', 1))
            
            if not code:
                continue
            
            # สร้าง barcode image (cache ต่อ barcode code)
            if code not in barcode_cache:
                try:
                    code_class = barcode_lib.get_barcode_class('code128')
                    bc_instance = code_class(str(code), writer=ImageWriter())
                    buf = BytesIO()
                    bc_instance.write(buf, options={
                        'module_width': 0.15 if cols >= 6 else 0.2,
                        'module_height': 5.0 if cols >= 6 else 6.0, # ปรับความสูงแถบให้เห็นชัด
                        'font_size': 0,
                        'text_distance': 1,
                        'quiet_zone': 0.5,
                        'write_text': False,
                    })
                    barcode_cache[code] = buf.getvalue()
                except Exception as e:
                    print(f"Barcode image gen fail for '{code}': {e}")
                    barcode_cache[code] = None
                
            # วนลูปตามจำนวนดวงที่ต้องการพิมพ์
            for _ in range(qty):
                label_story = []
                
                # 1. ชื่อสินค้า
                if show_name:
                    short_name = name[:26] + ".." if len(name) > 26 else name
                    label_story.append(Paragraph(short_name, name_style))
                
                # 2. แถบบาร์โค้ด (ปรับความสูงให้เต็มพื้นที่ดวง ไม่เหลือขอบบน-ล่างส่วนเกิน)
                bc_data = barcode_cache.get(code)
                if bc_data:
                    try:
                        bc_buf = BytesIO(bc_data)
                        bc_width = min(28*mm, cell_w - 3*mm)
                        bc_height = max(5.5*mm, cell_h * 0.45) # ปรับความสูงให้เต็ม 45% ของพื้นที่ดวงสติกเกอร์
                        img = RLImage(bc_buf, width=bc_width, height=bc_height)
                        img.hAlign = 'CENTER'
                        label_story.append(img)
                    except Exception as e:
                        print(f"Barcode embed fail: {e}")
                        label_story.append(Spacer(1, 5*mm))
                else:
                    label_story.append(Spacer(1, 5*mm))
                
                # 3. รหัสและราคา
                info_parts = []
                if show_code:
                    info_parts.append(code)
                if show_price:
                    try:
                        price_val = float(price)
                        info_parts.append(f"<b>฿{price_val:,.2f}</b>")
                    except (ValueError, TypeError):
                        info_parts.append(f"<b>฿{price}</b>")
                    
                if info_parts:
                    info_text = " ".join(info_parts)
                    label_story.append(Paragraph(info_text, info_style))
                    
                label_table = Table([ [label_story] ], colWidths=[cell_w], rowHeights=[cell_h])
                label_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0.2),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0.2),
                    ('TOPPADDING', (0,0), (-1,-1), 0.2),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0.2),
                ]))
                
                labels.append(label_table)
                
        if not labels:
            return False
            
        # จัดดวงป้ายทั้งหมดใส่ในโครงตารางหลัก (Grid)
        rows_data = []
        for i in range(0, len(labels), cols):
            chunk = labels[i:i+cols]
            while len(chunk) < cols:
                chunk.append(Paragraph("", name_style))
            rows_data.append(chunk)
            
        master_table = Table(
            rows_data, 
            colWidths=[cell_w] * cols,
            rowHeights=[cell_h] * len(rows_data)
        )
        master_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        story = [master_table]
        doc.build(story)
        return True
    except Exception as e:
        print(f"Error building barcode labels PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_full_receipt_a4(receipt_data, filename=None):
    """
    สร้างใบเสร็จรับเงิน/ใบกำกับภาษีเต็มรูปแบบ ขนาด A4 อย่างมืออาชีพ
    """
    register_thai_font()
    
    receipts_dir = Path("data/receipts")
    receipts_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        sale_number = receipt_data.get('sale_number', 'RECEIPT')
        filename = receipts_dir / f"receipt_A4_{sale_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    else:
        filename = Path(filename)
        if not filename.is_absolute() and "data" not in str(filename):
            filename = receipts_dir / filename
            
    if filename.parent:
        filename.parent.mkdir(parents=True, exist_ok=True)
        
    try:
        from reportlab.platypus import Image as RLImage
        from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
        import qrcode
        from io import BytesIO
        import os
        
        # ตั้งค่าขนาดเอกสาร A4 (210 x 297 mm) ระยะขอบ 15mm
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        styles = getSampleStyleSheet()
        
        # Styles
        normal_style = ParagraphStyle(
            'A4Normal',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT
        )
        
        normal_bold_style = ParagraphStyle(
            'A4NormalBold',
            parent=styles['Normal'],
            fontName='THSarabunBold',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT
        )
        
        right_style = ParagraphStyle(
            'A4Right',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=10,
            leading=12,
            alignment=TA_RIGHT
        )
        
        center_style = ParagraphStyle(
            'A4Center',
            parent=styles['Normal'],
            fontName='THSarabun',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER
        )
        
        title_style = ParagraphStyle(
            'A4Title',
            parent=styles['Normal'],
            fontName='THSarabunBold',
            fontSize=16,
            leading=19,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#1E3A8A')
        )
        
        story = []
        
        # === Header Section (2 Columns: Seller Info Left / Document Info Right) ===
        company_info = receipt_data.get('company', {})
        shop_name = company_info.get('name', 'ชื่อร้านค้า')
        shop_address = company_info.get('address', '-')
        shop_tax_id = company_info.get('tax_id', '-')
        shop_phone = company_info.get('phone', '-')
        shop_branch = company_info.get('branch', 'สำนักงานใหญ่')
        
        seller_html = f"<b>{shop_name}</b><br/>{shop_address}<br/>เลขประจำตัวผู้เสียภาษี: {shop_tax_id} ({shop_branch})<br/>โทร: {shop_phone}"
        seller_p = Paragraph(seller_html, normal_style)
        
        doc_title = Paragraph("<b>ใบเสร็จรับเงิน/ใบกำกับภาษี</b><br/><i>(Receipt / Tax Invoice)</i>", title_style)
        
        doc_details_html = f"""
        <b>เลขที่เอกสาร / No.:</b> {receipt_data.get('sale_number', '-')}<br/>
        <b>วันที่ / Date:</b> {receipt_data.get('sale_date', '-')}<br/>
        <b>วิธีชำระเงิน / Payment:</b> {receipt_data.get('payment_method', 'เงินสด')}<br/>
        <b>พนักงานขาย / Cashier:</b> {receipt_data.get('cashier', '-')}
        """
        doc_details_p = Paragraph(doc_details_html, normal_style)
        
        # ตาราง Header
        header_table_data = [
            [seller_p, doc_title],
            ['', doc_details_p]
        ]
        
        # colWidths: Left 90mm, Right 90mm
        header_table = Table(header_table_data, colWidths=[90*mm, 90*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('SPAN', (0, 0), (0, 1)), # รวมเซลล์ด้านซ้าย
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 4*mm))
        
        # === Buyer/Customer Info Section ===
        cust_name = receipt_data.get('customer_name') or 'ลูกค้าทั่วไป'
        cust_tax_id = receipt_data.get('customer_tax_id') or '-'
        cust_address = receipt_data.get('customer_address') or '-'
        
        buyer_html = f"""
        <b>ลูกค้า / Customer:</b> {cust_name}<br/>
        <b>ที่อยู่ / Address:</b> {cust_address}<br/>
        <b>เลขประจำตัวผู้เสียภาษี / Tax ID:</b> {cust_tax_id}
        """
        buyer_p = Paragraph(buyer_html, normal_style)
        
        buyer_table = Table([[buyer_p]], colWidths=[180*mm])
        buyer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(buyer_table)
        story.append(Spacer(1, 5*mm))
        
        # === Items Table ===
        # Columns: ลำดับ, รหัสสินค้า, รายการสินค้า, จำนวน, หน่วย, ราคาต่อหน่วย, ส่วนลด, จำนวนเงิน
        header_center_style = ParagraphStyle(
            'A4HeaderCenter',
            parent=styles['Normal'],
            fontName='THSarabunBold',
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.white
        )

        header_right_style = ParagraphStyle(
            'A4HeaderRight',
            parent=styles['Normal'],
            fontName='THSarabunBold',
            fontSize=11,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.white
        )

        items_header = [
            Paragraph("<b>ลำดับ</b>", header_center_style),
            Paragraph("<b>รหัสสินค้า</b>", header_center_style),
            Paragraph("<b>รายการสินค้า</b>", header_center_style),
            Paragraph("<b>จำนวน</b>", header_right_style),
            Paragraph("<b>หน่วย</b>", header_center_style),
            Paragraph("<b>ราคา/หน่วย</b>", header_right_style),
            Paragraph("<b>ส่วนลด</b>", header_right_style),
            Paragraph("<b>จำนวนเงิน</b>", header_right_style)
        ]
        
        items_table_data = [items_header]
        
        for idx, item in enumerate(receipt_data.get('items', []), 1):
            p_name = item.get('product_name', '-')
            p_barcode = item.get('barcode') or '-'
            qty = item.get('quantity', 0)
            unit = item.get('unit') or 'ชิ้น'
            price = item.get('unit_price', 0)
            discount = item.get('discount_amount', 0)
            total = item.get('total_price', 0)
            
            items_table_data.append([
                Paragraph(str(idx), center_style),
                Paragraph(str(p_barcode), center_style),
                Paragraph(p_name, normal_style),
                Paragraph(f"{qty:,}", right_style),
                Paragraph(unit, center_style),
                Paragraph(f"{price:,.2f}", right_style),
                Paragraph(f"{discount:,.2f}", right_style),
                Paragraph(f"{total:,.2f}", right_style)
            ])
            
        # เติมแถวว่างเฉพาะกรณีที่มีรายการน้อยกว่า 10 รายการ (เพื่อให้สวยงามในหน้าเดียว)
        if len(receipt_data.get('items', [])) < 10:
            blank_rows = 10 - len(receipt_data.get('items', []))
            for _ in range(blank_rows):
                items_table_data.append(['', '', '', '', '', '', '', ''])
            
        # colWidths: ลำดับ 12mm, รหัส 28mm, รายการ 50mm, จำนวน 15mm, หน่วย 13mm, ราคา/หน่วย 22mm, ส่วนลด 18mm, จำนวนเงิน 22mm
        # Total = 12+28+50+15+13+22+18+22 = 180mm
        # repeatRows=1 เพื่อให้แสดงหัวตารางซ้ำที่ด้านบนสุดของทุกหน้าโดยอัตโนมัติเมื่อมีหลายหน้า
        items_table = Table(
            items_table_data, 
            colWidths=[12*mm, 28*mm, 50*mm, 15*mm, 13*mm, 22*mm, 18*mm, 22*mm],
            repeatRows=1
        )
        items_table.setStyle(TableStyle([
            # Header Styling (Dark Blue)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Body Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 4*mm))
        
        # === Summary Section ===
        subtotal = receipt_data.get('subtotal', 0.0)
        discount_amount = receipt_data.get('discount_amount', 0.0)
        tax_amount = receipt_data.get('tax_amount', 0.0)
        total_amount = receipt_data.get('total_amount', 0.0)
        paid_amount = receipt_data.get('paid_amount', 0.0)
        change_amount = receipt_data.get('change_amount', 0.0)
        
        # คำนวณราคาไม่รวม VAT
        # ยอดก่อน VAT = ยอดสุทธิ - VAT
        net_subtotal = total_amount - tax_amount
        
        custom_note = receipt_data.get('note') or receipt_data.get('notes')
        if custom_note and str(custom_note).strip():
            note_text = str(custom_note).strip()
        else:
            note_text = "บันทึกรายละเอียดหัวบิลและสิทธิ์การใช้งานผ่านฐานข้อมูลและสำรองไว้ครบถ้วน"
            
        summary_left_html = f"<b>หมายเหตุ / Note:</b> {note_text}"
        summary_left_p = Paragraph(summary_left_html, normal_style)
        
        summary_right_data = [
            [Paragraph("<b>ยอดรวม / Subtotal:</b>", normal_style), Paragraph(f"฿{subtotal:,.2f}", right_style)],
            [Paragraph("<b>ส่วนลดบิล / Bill Discount:</b>", normal_style), Paragraph(f"฿{discount_amount:,.2f}", right_style)],
            [Paragraph("<b>ยอดก่อนภาษี / Subtotal Net:</b>", normal_style), Paragraph(f"฿{net_subtotal:,.2f}", right_style)],
            [Paragraph("<b>ภาษีมูลค่าเพิ่ม / VAT 7%:</b>", normal_style), Paragraph(f"฿{tax_amount:,.2f}", right_style)],
            [Paragraph("<b>ยอดสุทธิ / Total:</b>", normal_bold_style), Paragraph(f"฿{total_amount:,.2f}", right_style)],
            [Paragraph("<b>รับเงิน / Paid:</b>", normal_style), Paragraph(f"฿{paid_amount:,.2f}", right_style)],
            [Paragraph("<b>เงินทอน / Change:</b>", normal_bold_style), Paragraph(f"฿{change_amount:,.2f}", right_style)]
        ]
        summary_right_table = Table(summary_right_data, colWidths=[55*mm, 25*mm])
        summary_right_table.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LINEBELOW', (0, 3), (1, 3), 0.5, colors.HexColor('#CBD5E1')),
            ('LINEBELOW', (0, 4), (1, 4), 1, colors.HexColor('#1E3A8A')),
        ]))
        
        summary_table_data = [[summary_left_p, summary_right_table]]
        summary_table = Table(summary_table_data, colWidths=[100*mm, 80*mm])
        summary_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 6*mm))
        
        # === QR Code / Signatures Block ===
        qr_img_path = None
        # ค้นหาค่า PromptPay จากตาราง settings
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            qr_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
            db.disconnect()
            if qr_setting and qr_setting['setting_value'].strip():
                test_path = Path(qr_setting['setting_value'].strip())
                if test_path.exists():
                    qr_img_path = str(test_path)
        except Exception:
            pass
            
        if not qr_img_path:
            # สร้าง QR code อัตโนมัติ (ใส่ข้อมูลเลขที่บิลและยอดเงิน)
            try:
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(f"SaleNo: {receipt_data.get('sale_number')}\nTotal: {total_amount:,.2f}")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buf = BytesIO()
                img.save(buf, format='PNG')
                buf.seek(0)
                
                # เขียนใส่ temp
                os.makedirs("temp", exist_ok=True)
                qr_img_path = f"temp/qr_a4_{receipt_data.get('sale_number')}.png"
                with open(qr_img_path, 'wb') as f:
                    f.write(buf.getvalue())
            except Exception as e:
                print(f"Failed to generate custom QR: {e}")
                
        qr_flowable = None
        if qr_img_path and os.path.exists(qr_img_path):
            try:
                qr_flowable = RLImage(qr_img_path, width=28*mm, height=28*mm)
                qr_flowable.hAlign = 'CENTER'
            except Exception:
                pass
                
        # ส่วนเซ็นลายชื่อ
        sig_data = [
            [
                Paragraph("<b>ผู้รับเงิน / Collector</b>", center_style),
                Paragraph("<b>ลูกค้า / Customer</b>", center_style)
            ],
            ['', ''], # ช่องว่างเซ็น
            [
                Paragraph("_______________________<br/>วันที่: _____/_____/_____", center_style),
                Paragraph("_______________________<br/>วันที่: _____/_____/_____", center_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[65*mm, 65*mm], rowHeights=[6*mm, 15*mm, 10*mm])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        
        if qr_flowable:
            footer_table = Table([[qr_flowable, sig_table]], colWidths=[40*mm, 140*mm])
        else:
            footer_table = Table([[sig_table]], colWidths=[180*mm])
            
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(footer_table)
        
        # Build PDF
        doc.build(story)
        
        # ล้างไฟล์ QR temp ถ้าเพิ่งสร้างขึ้นมา
        if qr_img_path and "temp/qr_a4_" in qr_img_path and os.path.exists(qr_img_path):
            try:
                os.remove(qr_img_path)
            except Exception:
                pass
                
        return True, str(filename)
    except Exception as e:
        print(f"Error creating full A4 receipt PDF: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

