"""
Seed the master_orders table from the AC orders spreadsheet.

The spreadsheet is at:
  Documents/ac_interface_reference/Amazing charts interface/Order Sets/AC orders.xlsx

Usage:
    venv\Scripts\python.exe scripts/seed_master_orders.py

Requires openpyxl: pip install openpyxl
"""

import os
import sys

# Add project root to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from models.orderset import MasterOrder, ORDER_TABS


XLSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'Documents', 'ac_interface_reference', 'Amazing charts interface',
    'Order Sets', 'AC orders.xlsx',
)


def seed():
    if not os.path.exists(XLSX_PATH):
        print(f'Spreadsheet not found at: {XLSX_PATH}')
        print('Place the AC orders.xlsx file there and try again.')
        return

    try:
        import openpyxl
    except ImportError:
        print('openpyxl is required. Install it: pip install openpyxl')
        return

    app = create_app()
    with app.app_context():
        wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
        sheet = wb.active

        # The spreadsheet has 8 columns matching ORDER_TABS
        tab_names = ORDER_TABS

        added = 0
        skipped = 0

        for col_idx, tab_name in enumerate(tab_names, start=1):
            for row in sheet.iter_rows(min_row=2, min_col=col_idx,
                                        max_col=col_idx, values_only=False):
                cell = row[0]
                if cell.value is None or str(cell.value).strip() == '':
                    continue

                raw_name = str(cell.value).strip()

                # Try to extract CPT code if present (format: "Order Name (CPT123)")
                cpt_code = ''
                if '(' in raw_name and raw_name.endswith(')'):
                    parts = raw_name.rsplit('(', 1)
                    order_name = parts[0].strip()
                    cpt_code = parts[1].rstrip(')').strip()
                else:
                    order_name = raw_name

                existing = MasterOrder.query.filter_by(order_name=order_name).first()

                if existing:
                    if not existing.order_tab:
                        existing.order_tab = tab_name
                    if not existing.cpt_code and cpt_code:
                        existing.cpt_code = cpt_code
                    skipped += 1
                    continue

                new_order = MasterOrder(
                    order_name=order_name,
                    order_tab=tab_name,
                    order_label=order_name,
                    category=tab_name,
                    cpt_code=cpt_code,
                )
                db.session.add(new_order)
                added += 1

        db.session.commit()
        wb.close()

        print(f'Seed complete: {added} orders added, {skipped} skipped (already exist).')
        total = MasterOrder.query.count()
        print(f'Total master orders in database: {total}')


if __name__ == '__main__':
    seed()
