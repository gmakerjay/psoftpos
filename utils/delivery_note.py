# -*- coding: utf-8 -*-
"""
Delivery Note Generator - สร้างใบส่งของ/ใบกำกับสินค้า
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
try:
    from .pdf_utils import register_thai_font
except ImportError:
    from pdf_utils import register_thai_font


class DeliveryNoteGenerator:
    """สร้างใบส่งของ (Delivery Note)"""
    
    def __init__(self, shop_info):
        """
        shop_info = {
            'name': 'ชื่อร้าน',
            'address': 'ที่อยู่',
            'tel': 'เบอร์โทร'
        }
        """
        self.shop_info = shop_info
        
        # สร้างโฟลเดอร์เก็บ PDF
        os.makedirs("data/delivery_notes", exist_ok=True)
    
    def generate_delivery_number(self):
        """สร้างเลขที่ใบส่งของ: DN-YYYYMMDD-XXXX"""
        today = datetime.now().strftime("%Y%m%d")
        
        # นับจำนวนไฟล์ในวันนี้
        files = os.listdir("data/delivery_notes")
        today_files = [f for f in files if f.startswith(f"DN-{today}")]
        sequence = len(today_files) + 1
        
        return f"DN-{today}-{sequence:04d}"
    
    def create_delivery_note(self, delivery_data):
        """
        สร้างใบส่งของ
        
        delivery_data = {
            'delivery_date': '2024-12-05',
            'sender_name': 'ชื่อผู้ส่ง',
            'sender_address': 'ที่อยู่ผู้ส่ง',
            'sender_tel': 'เบอร์โทร',
            'receiver_name': 'ชื่อผู้รับ',
            'receiver_address': 'ที่อยู่ผู้รับ',
            'receiver_tel': 'เบอร์โทร',
            'items': [
                {
                    'product_name': 'สินค้า A',
                    'quantity': 2,
                    'unit': 'ชิ้น',
                    'note': 'หมายเหตุ'
                }
            ],
            'delivery_method': 'รถส่งของ / ไปรษณีย์ / อื่นๆ',
            'note': 'หมายเหตุเพิ่มเติม'
        }
        """
        register_thai_font()
        delivery_no = self.generate_delivery_number()
        delivery_date = datetime.strptime(delivery_data['delivery_date'], "%Y-%m-%d")
        
        # สร้าง PDF
        pdf_path = f"data/delivery_notes/{delivery_no}.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                leftMargin=15*mm, rightMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        
        story = []
        
        # === Header ===
        story.append(Spacer(1, 10*mm))
        
        # ชื่อเอกสาร
        title_style = ParagraphStyle(
            'Title',
            fontSize=22,
            alignment=TA_CENTER,
            fontName='THSarabunBold',
            textColor=colors.HexColor('#2E7D32')
        )
        story.append(Paragraph("<b>ใบส่งของ / Delivery Note</b>", title_style))
        story.append(Spacer(1, 3*mm))
        
        # เลขที่ใบส่งของ
        dn_style = ParagraphStyle(
            'DNNo',
            fontSize=14,
            alignment=TA_CENTER,
            fontName='THSarabun'
        )
        story.append(Paragraph(f"เลขที่ / No.: <b>{delivery_no}</b>", dn_style))
        story.append(Paragraph(f"วันที่ / Date: <b>{delivery_date.strftime('%d/%m/%Y')}</b>", dn_style))
        story.append(Spacer(1, 5*mm))
        
        # === ข้อมูลผู้ส่ง-ผู้รับ ===
        info_data = [
            # ผู้ส่ง
            [
                Paragraph("<b>ผู้ส่ง / Sender:</b>", ParagraphStyle('Normal', fontSize=12, fontName='THSarabunBold')),
                Paragraph("<b>ผู้รับ / Receiver:</b>", ParagraphStyle('Normal', fontSize=12, fontName='THSarabunBold'))
            ],
            [
                Paragraph(f"<b>{delivery_data['sender_name']}</b>", ParagraphStyle('Normal', fontSize=11, fontName='THSarabun')),
                Paragraph(f"<b>{delivery_data['receiver_name']}</b>", ParagraphStyle('Normal', fontSize=11, fontName='THSarabun'))
            ],
            [
                Paragraph(f"{delivery_data['sender_address']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabun')),
                Paragraph(f"{delivery_data['receiver_address']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabun'))
            ],
            [
                Paragraph(f"โทร: {delivery_data['sender_tel']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabun')),
                Paragraph(f"โทร: {delivery_data['receiver_tel']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabun'))
            ]
        ]
        
        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('BOX', (0, 0), (0, -1), 1, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 5*mm))
        
        # วิธีการจัดส่ง
        delivery_method_data = [[
            Paragraph(f"<b>วิธีการจัดส่ง:</b> {delivery_data.get('delivery_method', '-')}", 
                      ParagraphStyle('Normal', fontSize=11, fontName='THSarabun'))
        ]]
        
        dm_table = Table(delivery_method_data, colWidths=[180*mm])
        dm_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(dm_table)
        story.append(Spacer(1, 5*mm))
        
        # === ตารางสินค้า ===
        items_data = [
            ['ลำดับ', 'รายการสินค้า', 'จำนวน', 'หน่วย', 'หมายเหตุ']
        ]
        
        for i, item in enumerate(delivery_data['items'], 1):
            items_data.append([
                str(i),
                item['product_name'],
                f"{item['quantity']:.2f}",
                item.get('unit', 'ชิ้น'),
                item.get('note', '')
            ])
        
        # เว้นบรรทัดว่าง
        for _ in range(max(0, 12 - len(delivery_data['items']))):
            items_data.append(['', '', '', '', ''])
        
        items_table = Table(items_data, colWidths=[15*mm, 80*mm, 25*mm, 20*mm, 40*mm])
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'THSarabunBold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'THSarabun'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # ลำดับ
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # รายการ
            ('ALIGN', (2, 1), (3, -1), 'CENTER'),  # จำนวน/หน่วย
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),    # หมายเหตุ
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 5*mm))
        
        # หมายเหตุเพิ่มเติม
        if delivery_data.get('note'):
            note_data = [[
                Paragraph(f"<b>หมายเหตุ:</b> {delivery_data['note']}", 
                          ParagraphStyle('Normal', fontSize=10, fontName='THSarabun'))
            ]]
            
            note_table = Table(note_data, colWidths=[180*mm])
            note_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFDE7')),
            ]))
            story.append(note_table)
            story.append(Spacer(1, 5*mm))
        
        # === ลายเซ็น ===
        story.append(Spacer(1, 10*mm))
        
        signature_data = [
            [
                Paragraph("<b>ผู้ส่งของ / Sender</b>", 
                          ParagraphStyle('Center', fontSize=11, alignment=TA_CENTER, fontName='THSarabunBold')),
                Paragraph("<b>ผู้รับของ / Receiver</b>", 
                          ParagraphStyle('Center', fontSize=11, alignment=TA_CENTER, fontName='THSarabunBold')),
                Paragraph("<b>ผู้อนุมัติ / Approved By</b>", 
                          ParagraphStyle('Center', fontSize=11, alignment=TA_CENTER, fontName='THSarabunBold'))
            ],
            ['', '', ''],  # ช่องว่างสำหรับลายเซ็น
            [
                Paragraph("_______________________", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun')),
                Paragraph("_______________________", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun')),
                Paragraph("_______________________", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun'))
            ],
            [
                Paragraph("( ______________________ )", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun')),
                Paragraph("( ______________________ )", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun')),
                Paragraph("( ______________________ )", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun'))
            ],
            [
                Paragraph("วันที่: _____/_____/_____", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun')),
                Paragraph("วันที่: _____/_____/_____", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun')),
                Paragraph("วันที่: _____/_____/_____", 
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabun'))
            ]
        ]
        
        signature_table = Table(signature_data, colWidths=[60*mm, 60*mm, 60*mm], rowHeights=[10*mm, 20*mm, 8*mm, 8*mm, 8*mm])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
        ]))
        story.append(signature_table)
        
        # สร้าง PDF
        doc.build(story)
        
        return pdf_path, delivery_no


# ทดสอบ
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    # ข้อมูลร้าน
    shop_info = {
        'name': 'บริษัท ตัวอย่าง จำกัด',
        'address': '123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110',
        'tel': '02-123-4567'
    }
    
    # ข้อมูลการจัดส่ง
    delivery_data = {
        'delivery_date': datetime.now().strftime("%Y-%m-%d"),
        'sender_name': shop_info['name'],
        'sender_address': shop_info['address'],
        'sender_tel': shop_info['tel'],
        'receiver_name': 'บริษัท ลูกค้า จำกัด',
        'receiver_address': '456 ถนนเพชรบุรี แขวงมักกะสัน เขตราชเทวี กรุงเทพฯ 10400',
        'receiver_tel': '02-987-6543',
        'items': [
            {
                'product_name': 'โทรศัพท์มือถือ Samsung Galaxy S23',
                'quantity': 5,
                'unit': 'เครื่อง',
                'note': 'สีดำ'
            },
            {
                'product_name': 'เคสโทรศัพท์',
                'quantity': 5,
                'unit': 'อัน',
                'note': 'สีใส'
            },
            {
                'product_name': 'ฟิล์มกระจก',
                'quantity': 10,
                'unit': 'แผ่น',
                'note': ''
            }
        ],
        'delivery_method': 'รถส่งของของบริษัท',
        'note': 'ขอเซ็นรับของภายใน 3 วันนับจากวันที่ส่งของ'
    }
    
    # สร้างใบส่งของ
    generator = DeliveryNoteGenerator(shop_info)
    
    try:
        pdf_path, delivery_no = generator.create_delivery_note(delivery_data)
        print(f"✅ สร้างใบส่งของสำเร็จ!")
        print(f"📄 เลขที่: {delivery_no}")
        print(f"💾 ไฟล์: {pdf_path}")
        
        # เปิดไฟล์
        os.startfile(os.path.abspath(pdf_path))
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
