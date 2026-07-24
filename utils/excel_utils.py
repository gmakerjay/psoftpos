# -*- coding: utf-8 -*-
"""
ฟังก์ชันสำหรับจัดการ Excel (Import/Export)
"""


from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
from pathlib import Path


class ExcelManager:
    """จัดการการ Import/Export ข้อมูล Excel"""
    
    @staticmethod
    def export_to_excel(data, columns, filename, sheet_name="Sheet1", title=None):
        """
        Export ข้อมูลเป็นไฟล์ Excel
        
        Args:
            data: ข้อมูลแบบ list of dict หรือ list of list
            columns: ชื่อคอลัมน์
            filename: ชื่อไฟล์
            sheet_name: ชื่อ sheet
            title: หัวข้อรายงาน
            
        Returns:
            True ถ้าสำเร็จ
        """
        try:
            # สร้าง workbook
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            
            # กำหนดสไตล์
            header_font = Font(bold=True, color="FFFFFF", size=12)
            header_fill = PatternFill(start_color="1F538D", end_color="1F538D", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            current_row = 1
            
            # เพิ่มหัวข้อ
            if title:
                ws.merge_cells(f'A1:{chr(64 + len(columns))}1')
                title_cell = ws['A1']
                title_cell.value = title
                title_cell.font = Font(bold=True, size=16)
                title_cell.alignment = Alignment(horizontal='center')
                current_row = 2
                
                # วันที่สร้างรายงาน
                ws.merge_cells(f'A2:{chr(64 + len(columns))}2')
                date_cell = ws['A2']
                date_cell.value = f"วันที่: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                date_cell.alignment = Alignment(horizontal='center')
                current_row = 4
            
            # เพิ่ม header
            for col_idx, column in enumerate(columns, start=1):
                cell = ws.cell(row=current_row, column=col_idx)
                cell.value = column
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = border
            
            # เพิ่มข้อมูล
            for row_data in data:
                current_row += 1
                if isinstance(row_data, dict):
                    # ถ้าเป็น dict ใช้ key ตาม columns
                    for col_idx, column in enumerate(columns, start=1):
                        cell = ws.cell(row=current_row, column=col_idx)
                        cell.value = row_data.get(column, "")
                        cell.border = border
                else:
                    # ถ้าเป็น list
                    for col_idx, value in enumerate(row_data, start=1):
                        cell = ws.cell(row=current_row, column=col_idx)
                        cell.value = value
                        cell.border = border
            
            # ปรับความกว้างคอลัมน์
            from openpyxl.utils import get_column_letter
            for column in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # บันทึกไฟล์
            wb.save(filename)
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    @staticmethod
    def import_from_excel(filename, sheet_name=0, header_row=0):
        """
        Import ข้อมูลจากไฟล์ Excel
        
        Args:
            filename: ชื่อไฟล์
            sheet_name: ชื่อหรือ index ของ sheet
            header_row: แถวที่เป็น header (0-based)
            
        Returns:
            list of dict
        """
        try:
            import pandas as pd
            clean_path = str(Path(filename).resolve())
            df = pd.read_excel(clean_path, sheet_name=sheet_name, header=header_row)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error importing from Excel: {e}")
            raise e
    
    @staticmethod
    def export_products_template():
        """สร้าง template สำหรับ import สินค้า"""
        columns = [
            "บาร์โค้ด",
            "ชื่อสินค้า",
            "หมวดหมู่",
            "ราคาทุน",
            "ราคาขายปกติ",
            "ราคาขายส่ง",
            "ราคาพิเศษ1",
            "ราคาพิเศษ2",
            "จำนวนสต็อก",
            "สต็อกขั้นต่ำ",
            "หน่วย"
        ]
        
        # ข้อมูลตัวอย่าง
        sample_data = [
            {
                "บาร์โค้ด": "8851234567890",
                "ชื่อสินค้า": "สินค้าตัวอย่าง 1",
                "หมวดหมู่": "อาหารและเครื่องดื่ม",
                "ราคาทุน": 50.00,
                "ราคาขายปกติ": 80.00,
                "ราคาขายส่ง": 70.00,
                "ราคาพิเศษ1": 75.00,
                "ราคาพิเศษ2": 65.00,
                "จำนวนสต็อก": 100,
                "สต็อกขั้นต่ำ": 10,
                "หน่วย": "ชิ้น"
            }
        ]
        
        filename = f"template_สินค้า_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return ExcelManager.export_to_excel(
            sample_data,
            columns,
            filename,
            "สินค้า",
            "Template สำหรับ Import สินค้า"
        )


def export_sales_report(sales_data, filename=None):
    """
    Export รายงานยอดขาย
    
    Args:
        sales_data: ข้อมูลการขาย (list of dict)
        filename: ชื่อไฟล์ (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
    """
    if filename is None:
        filename = f"รายงานยอดขาย_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    columns = [
        "เลขที่ใบเสร็จ",
        "วันที่",
        "ลูกค้า",
        "ยอดรวม",
        "ส่วนลด",
        "ยอดสุทธิ",
        "พนักงานขาย",
        "สถานะ"
    ]
    
    manager = ExcelManager()
    return manager.export_to_excel(
        sales_data,
        columns,
        filename,
        "รายงานยอดขาย",
        "รายงานยอดขาย"
    )


def export_products_list(products_data, filename=None):
    """Export รายการสินค้า"""
    if filename is None:
        filename = f"รายการสินค้า_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    columns = [
        "บาร์โค้ด",
        "ชื่อสินค้า",
        "หมวดหมู่",
        "ราคาทุน",
        "ราคาขาย",
        "สต็อก",
        "สถานะ"
    ]
    
    manager = ExcelManager()
    return manager.export_to_excel(
        products_data,
        columns,
        filename,
        "รายการสินค้า",
        "รายการสินค้าทั้งหมด"
    )


if __name__ == "__main__":
    # ทดสอบ
    print("สร้าง Template สำหรับ Import สินค้า...")
    if ExcelManager.export_products_template():
        print("สร้าง Template สำเร็จ!")
    else:
        print("สร้าง Template ไม่สำเร็จ")
