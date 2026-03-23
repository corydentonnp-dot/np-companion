"""Add PDMP and VIIS credential columns to User table."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

COLUMNS = [
    ('users', 'pdmp_username_enc', 'TEXT DEFAULT ""'),
    ('users', 'pdmp_password_enc', 'TEXT DEFAULT ""'),
    ('users', 'viis_username_enc', 'TEXT DEFAULT ""'),
    ('users', 'viis_password_enc', 'TEXT DEFAULT ""'),
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for table, col, col_type in COLUMNS:
        try:
            cur.execute(f'ALTER TABLE "{table}" ADD COLUMN {col} {col_type}')
            print(f'  Added {table}.{col}')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print(f'  {table}.{col} already exists — skipping')
            else:
                raise
    conn.commit()
    conn.close()
    print('Migration complete.')

if __name__ == '__main__':
    migrate()
